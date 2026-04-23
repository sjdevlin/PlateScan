from datetime import datetime

from hardware import CameraControllerFactory, FocusControllerFactory, IlluminationControllerFactory, StageControllerFactory
from services import AppConfig, Logger, row_label_to_index


class ImageSandboxPresenter:
    def __init__(self, view, db):
        self.view = view
        self.db = db
        self.logger = Logger()
        self.app_config = AppConfig()

        camera_type = self.app_config.get("camera_type")
        self.camera_controller = CameraControllerFactory.create_camera_controller(camera_type)
        self.stage_controller = StageControllerFactory.create_stage_controller()
        self.illumination_controller = IlluminationControllerFactory.create_illumination_controller()
        self.focus_controller = FocusControllerFactory.create_focus_controller()
        self.dry_run = bool(self.app_config.get("dry_run", False))

        self.plates = self.db.get_all_plates()
        self.plate_lookup = {self._plate_option_label(plate): plate for plate in self.plates}

        self.current_plate = None
        self.current_default_focus = None
        self.selected_well = None
        self.moved_to_well = None

        self.view.bind_plate_change(self.on_plate_selected)
        self.view.move_button.configure(command=self.move_to_well)
        self.view.image_button.configure(command=self.capture_image)

        self._init_defaults()
        self._init_plate_options()
        if self.dry_run:
            self.view.display_info("Image Sandbox is running in dry-run mode.")

    def _init_defaults(self):
        default_led_number = self.app_config.get("sandbox_led_number", 2)
        default_led_intensity = self.app_config.get("sandbox_led_intensity", 1.0)
        default_exposure = self.app_config.get("exposure_time", 200000)
        default_autofocus = bool(self.app_config.get("sandbox_autofocus", False))

        self.view.set_default_controls(
            led_number=default_led_number,
            led_intensity=default_led_intensity,
            exposure_time=default_exposure,
            autofocus=default_autofocus,
        )

    def _init_plate_options(self):
        options = ["Select Plate"] + [self._plate_option_label(plate) for plate in self.plates]
        self.view.set_plate_options(options)

    @staticmethod
    def _plate_option_label(plate):
        return f"{plate.id}: {plate.description}"

    def on_plate_selected(self, selected_option):
        plate = self.plate_lookup.get(selected_option)
        if plate is None:
            return

        self.current_plate = plate
        self.current_default_focus = self._get_plate_default_focus(plate)
        self.selected_well = None
        self.moved_to_well = None
        self.view.set_move_enabled(False)
        self.view.set_image_enabled(False)
        self.view.selection_label.configure(text="No well selected")

        self._apply_default_focus_for_plate()
        self.view.show_plate(self.current_plate, self.selected_well, self.on_well_clicked)

    def on_well_clicked(self, event):
        if self.current_plate is None:
            return

        clicked = self.view.get_clicked_well(event)
        if clicked is None:
            return

        self.selected_well = clicked
        self.moved_to_well = None
        self.view.set_selected_well(*self.selected_well)
        self.view.set_move_enabled(True)
        self.view.set_image_enabled(False)
        self.view.show_plate(self.current_plate, self.selected_well, self.on_well_clicked)

    def move_to_well(self):
        if self.current_plate is None or self.selected_well is None:
            self.view.display_error("Please select a plate and a well.")
            return

        row_label, col_number = self.selected_well
        row_index = row_label_to_index(row_label)
        col_index = int(col_number) - 1

        x = float(self.current_plate.centre_first_well_offset_x or 0) + (
            col_index * float(self.current_plate.well_spacing_x or 0)
        )
        y = float(self.current_plate.centre_first_well_offset_y or 0) + (
            row_index * float(self.current_plate.well_spacing_y or 0)
        )

        try:
            self.stage_controller.move(position=x, axis="x", speed="normal")
            self.stage_controller.move(position=y, axis="y", speed="normal")
            self._apply_default_focus_for_plate()
        except Exception as exc:
            self.logger.error(f"Failed to move stage: {exc}")
            self.view.display_error(f"Failed to move stage: {exc}")
            return

        self.moved_to_well = self.selected_well
        self.view.set_image_enabled(True)

    def capture_image(self):
        if self.moved_to_well is None:
            self.view.display_error("Move to a selected well before imaging.")
            return

        try:
            led_number = int(self.view.led_number_entry.get().strip())
            led_intensity = float(self.view.led_intensity_entry.get().strip())
            exposure_time = int(float(self.view.exposure_entry.get().strip()))
        except Exception:
            self.view.display_error("LED number, intensity, and exposure time must be numeric.")
            return

        autofocus_enabled = self.view.autofocus_switch.get() == 1

        try:
            self.illumination_controller.illumination_setup(led_number, led_intensity)
            self.illumination_controller.illumination_enable(self._led_number_to_bitmask(led_number), hex_mode=True)

            self.camera_controller.set_exposure_time(exposure_time)

            if autofocus_enabled:
                self.focus_controller.autofocus(True)
                self.focus_controller.autofocus(False)

            row_label, col_number = self.moved_to_well
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_stub = f"sandbox_{row_label}{col_number}_{timestamp}"
            image_dir = self.app_config.get("image_file_directory", ".")
            self.camera_controller.set_filename(f"{image_dir}/{image_stub}")
            self.camera_controller.capture_image()

            self.view.display_info(f"Image captured for well {row_label}{col_number}.")
            self.view.set_image_enabled(True)

        except Exception as exc:
            self.logger.error(f"Failed to capture image: {exc}")
            self.view.display_error(f"Failed to capture image: {exc}")

    @staticmethod
    def _led_number_to_bitmask(led_number):
        return hex(1 << int(led_number))

    @staticmethod
    def _get_plate_default_focus(plate):
        if plate is None:
            return None
        if getattr(plate, "default_focus", None) is None:
            return None
        return float(plate.default_focus)

    def _apply_default_focus_for_plate(self):
        if self.current_default_focus is None:
            return

        try:
            self.focus_controller.autofocus(False)
            self.focus_controller.move_z(self.current_default_focus)
            self.logger.info(
                f"Applied default focus {self.current_default_focus:.2f} for plate {self.current_plate.id}"
            )
        except Exception as exc:
            self.logger.error(f"Failed to apply default focus: {exc}")
            self.view.display_error(f"Failed to apply default focus: {exc}")
