from datetime import datetime
from pathlib import Path
from time import sleep
import random

from PIL import Image as PilImage, ImageDraw

from hardware import CameraControllerFactory, FocusControllerFactory, IlluminationControllerFactory, StageControllerFactory
from models import Image, ResultRun
from services import AppConfig, Logger, Movie2Tiff, index_to_row_label, normalize_well_list, parse_well_designator


class RunStopped(Exception):
    pass


class ResultRunOperator:
    def __init__(self, plate, image_set, run_description, db, stop_event=None, error_callback=None):
        self.db = db
        self.logger = Logger()
        self.app_config = AppConfig()
        self.dry_run = bool(self.app_config.get("dry_run", False))
        self.plate = plate
        self.image_set = image_set
        self.run_description = run_description
        self.stop_event = stop_event
        self.error_callback = error_callback

        self.converter = Movie2Tiff()

        self.number_of_sites = max(1, int(self.image_set.number_of_sites or 1))
        self.stack_size = max(1, int(self.image_set.stack_size or 1))
        self.stack_step_size = int(self.image_set.stack_step_size or 1)

        self.well_list = normalize_well_list(self.image_set.wells or "")
        self._validate_wells_fit_plate()

        camera_type = self.app_config.get("camera_type", "FLIR")
        self.camera_controller = CameraControllerFactory.create_camera_controller(camera_type)
        self.stage_controller = StageControllerFactory.create_stage_controller()
        self.illumination_controller = IlluminationControllerFactory.create_illumination_controller()
        self.focus_controller = FocusControllerFactory.create_focus_controller()

        self.channel_1_number = self.image_set.channel_1_number
        self.channel_1_intensity = self.image_set.channel_1_intensity
        self.channel_2_number = self.image_set.channel_2_number
        self.channel_2_intensity = self.image_set.channel_2_intensity

        self.active_channels = [
            {
                "number": int(self.channel_1_number),
                "intensity": float(self.channel_1_intensity),
                "bitmask": self._led_number_to_bitmask(self.channel_1_number),
            }
        ]
        if self.channel_2_number is not None and self.channel_2_intensity is not None:
            self.active_channels.append(
                {
                    "number": int(self.channel_2_number),
                    "intensity": float(self.channel_2_intensity),
                    "bitmask": self._led_number_to_bitmask(self.channel_2_number),
                }
            )

        for channel in self.active_channels:
            self.illumination_controller.illumination_setup(channel["number"], channel["intensity"])

        self.camera_controller.set_exposure_time(int(self.app_config.get("exposure_time", 200000)))
        self.movie_path = self.app_config.get("movie_file_directory", "./")
        self.image_path = self.app_config.get("image_file_directory", "./")

        if not self._ensure_output_dirs():
            raise RuntimeError("Output directories are not writable")

        self.result_run_id = self.db.add_result_run(
            ResultRun(
                plate_id=self.plate.id,
                image_set_id=self.image_set.id,
                description=self.run_description,
                start_date_time=self._local_minute_now(),
                status="Running",
            )
        )

        self.result_run = self.db.get_result_run_by_id(self.result_run_id)
        self.focus_position = None
        self.site_offsets = self._build_site_offsets()

    def request_stop(self, reason="Run stop requested"):
        self.logger.warning(reason)
        if self.stop_event is not None:
            self.stop_event.set()

    def run(self):
        try:
            self._raise_if_stopped()
            self.logger.info("Camera trigger enabled")
            self.camera_controller.set_trigger()
            if self.dry_run:
                self.logger.info("Result run operator is executing in dry-run mode.")

            self.focus_position = self.focus_controller.get_z()
            self.logger.info(f"Initial focus z set to {self.focus_position:.2f}")

            for well in self.well_list:
                self._raise_if_stopped()
                row_index, col_index = parse_well_designator(well)
                row_label = index_to_row_label(row_index)
                column_number = col_index + 1

                for site_number in range(self.number_of_sites):
                    self._raise_if_stopped()

                    movie_stub = f"{self.movie_path}/{self.result_run.id}_{well}_{site_number}"
                    image_stub = f"{self.image_path}/{self.result_run.id}_{well}_{site_number}"
                    self.camera_controller.set_filename(movie_stub)

                    self._move_stage_to_site(row_index, col_index, site_number)
                    self.focus_controller.move_z(self.focus_position)

                    self._take_stack()
                    movie_filename = f"{movie_stub}{self.app_config.get('movie_extension', '.movie')}"
                    self._process_stack(movie_filename, image_stub, row_label, column_number, site_number)

            self.result_run.status = "Complete"

        except RunStopped:
            if self.result_run.status == "Running":
                self.result_run.status = "Aborted"
            self.logger.warning("Imaging run stopped")

        except Exception as exc:
            self.result_run.status = "Failed"
            self.logger.error(f"Imaging run failed: {exc}")
            self._notify_error("imaging", exc)

        finally:
            self.result_run.finish_date_time = self._local_minute_now()
            try:
                self.db.update_result_run(self.result_run)
            except Exception as exc:
                self.logger.error(f"Failed to persist run status: {exc}")

            try:
                self.illumination_controller.illumination_enable(0x00, hex_mode=True)
            except Exception as exc:
                self.logger.error(f"Failed to switch off illumination: {exc}")

            try:
                self.camera_controller.stop_recording()
            except Exception:
                pass

            self.logger.info(f"Imaging thread exited with status: {self.result_run.status}")

    def _validate_wells_fit_plate(self):
        num_rows = int(self.plate.num_rows or 0)
        num_cols = int(self.plate.num_cols or 0)
        invalid = []

        for well in self.well_list:
            row_index, col_index = parse_well_designator(well)
            if row_index >= num_rows or col_index >= num_cols:
                invalid.append(well)

        if invalid:
            raise ValueError(
                f"ImageSet contains wells outside selected plate geometry ({num_rows}x{num_cols}): {', '.join(invalid)}"
            )

    def _move_stage_to_site(self, row_index, col_index, site_number):
        x = self.plate.centre_first_well_offset_x + (col_index * self.plate.well_spacing_x)
        y = self.plate.centre_first_well_offset_y + (row_index * self.plate.well_spacing_y)

        if site_number < len(self.site_offsets):
            offset_x, offset_y = self.site_offsets[site_number]
        else:
            offset_x, offset_y = (0.0, 0.0)

        x += offset_x
        y += offset_y

        self.stage_controller.move(position=x, axis="x", speed="normal")
        self.stage_controller.move(position=y, axis="y", speed="normal")
        sleep(1)

    def _take_stack(self):
        self.camera_controller.start_recording()

        for stack_index in range(self.stack_size):
            self._raise_if_stopped()

            if stack_index > 0 and self.stack_step_size:
                new_z = self.focus_controller.get_z() + self.stack_step_size
                self.focus_controller.move_z(new_z, speed="normal")

            for channel in self.active_channels:
                self.illumination_controller.illumination_enable(channel["bitmask"], hex_mode=True)
                self.camera_controller.capture_image()

        self.camera_controller.stop_recording()

    def _process_stack(self, movie_filename, image_stub, well_row, well_column, site_number):
        if self.dry_run:
            self._process_stack_dry_run(image_stub, well_row, well_column, site_number)
            return

        filenames, focus_scores = self.converter.convert(movie_name=movie_filename, file_stub=image_stub)
        channel_count = max(1, len(self.active_channels))

        for idx, (file, score) in enumerate(zip(filenames, focus_scores)):
            file_path = Path(str(file)).name
            channel = self.active_channels[idx % channel_count]
            z_stack_number = idx // channel_count

            new_image = Image(
                result_run_id=self.result_run.id,
                well_row=well_row,
                well_column=well_column,
                site_number=site_number,
                stack_number=z_stack_number,
                led_number=channel["number"],
                dimension_x=getattr(self.camera_controller, "image_dimension_x", 0),
                dimension_y=getattr(self.camera_controller, "image_dimension_y", 0),
                file_path=file_path,
                timestamp=datetime.now(),
                focus_score=score,
            )
            self.db.add_result_run_image(new_image)

    def _process_stack_dry_run(self, image_stub, well_row, well_column, site_number):
        image_stub_path = Path(image_stub)
        output_dir = image_stub_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        frame_counter = 0
        for stack_number in range(self.stack_size):
            for channel in self.active_channels:
                frame_counter += 1
                filename = output_dir / f"{image_stub_path.name}_{frame_counter:03d}.png"
                focus_score = float((self.stack_size - stack_number) * 10 + channel["number"])
                self._write_mock_image(
                    file_path=filename,
                    well_row=well_row,
                    well_column=well_column,
                    site_number=site_number,
                    stack_number=stack_number,
                    channel_number=channel["number"],
                )

                new_image = Image(
                    result_run_id=self.result_run.id,
                    well_row=well_row,
                    well_column=well_column,
                    site_number=site_number,
                    stack_number=stack_number,
                    led_number=channel["number"],
                    dimension_x=getattr(self.camera_controller, "image_dimension_x", 512),
                    dimension_y=getattr(self.camera_controller, "image_dimension_y", 512),
                    file_path=filename.name,
                    timestamp=datetime.now(),
                    focus_score=focus_score,
                )
                self.db.add_result_run_image(new_image)

    def _write_mock_image(self, file_path, well_row, well_column, site_number, stack_number, channel_number):
        width = int(getattr(self.camera_controller, "image_dimension_x", 512) or 512)
        height = int(getattr(self.camera_controller, "image_dimension_y", 512) or 512)

        image = PilImage.new("L", (width, height), color=40)
        draw = ImageDraw.Draw(image)
        text = f"{well_row}{well_column} S{site_number} Z{stack_number} C{channel_number}"
        draw.rectangle([(20, 20), (width - 20, height - 20)], outline=180, width=2)
        draw.text((30, 30), text, fill=220)
        image.save(file_path)

    def _ensure_output_dirs(self):
        for path in (self.movie_path, self.image_path):
            p = Path(path).expanduser()
            try:
                p.mkdir(parents=True, exist_ok=True)
                test_file = p / ".write_test"
                test_file.write_text("ok")
                test_file.unlink(missing_ok=True)
            except Exception as exc:
                self.logger.error(f"Output path not writable: {p} ({exc})")
                return False
        return True

    def _stop_requested(self):
        return self.stop_event is not None and self.stop_event.is_set()

    def _raise_if_stopped(self):
        if self._stop_requested():
            raise RunStopped()

    def _notify_error(self, source, exc):
        if self.stop_event is not None:
            self.stop_event.set()
        if callable(self.error_callback):
            try:
                self.error_callback(source, str(exc))
            except Exception:
                pass

    def _build_site_offsets(self):
        if self.number_of_sites <= 0:
            return [(0.0, 0.0)]

        well_diameter = float(self.plate.well_dimension or 0.0)
        offset_limit = well_diameter * 0.10
        offsets = [(0.0, 0.0)]

        for _ in range(1, self.number_of_sites):
            offsets.append(
                (
                    random.uniform(-offset_limit, offset_limit),
                    random.uniform(-offset_limit, offset_limit),
                )
            )

        return offsets

    @staticmethod
    def _local_minute_now():
        return datetime.now().replace(second=0, microsecond=0)

    @staticmethod
    def _led_number_to_bitmask(led_number):
        return hex(1 << int(led_number))
