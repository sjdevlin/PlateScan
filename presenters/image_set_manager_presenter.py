import re
from copy import deepcopy
from tkinter import messagebox

from models import ImageSet
from services import normalize_well_list, serialize_well_list, wells_fit_plate_geometry
from views import ImageSetDetailView


class ImageSetManagerPresenter:
    def __init__(self, view, db):
        self.view = view
        self.db = db

        self.view.bind_row_selection(self.on_row_selected)
        self.view.new_button.configure(command=self.create_image_set)
        self.view.edit_button.configure(command=self.edit_image_set)
        self.view.copy_button.configure(command=self.copy_image_set)
        self.view.delete_button.configure(command=self.delete_image_set)

        self.selected_id = None
        self.refresh_view()

    def refresh_view(self):
        image_sets = self.db.get_all_image_sets()
        rows = []
        for image_set in image_sets:
            rows.append(
                (
                    image_set.id,
                    image_set.description,
                    image_set.number_of_sites,
                    image_set.stack_size,
                    image_set.stack_step_size,
                    "" if image_set.channel_1_number is None else str(image_set.channel_1_number),
                    "" if image_set.channel_2_number is None else str(image_set.channel_2_number),
                )
            )

        self.view.list_image_sets(rows)
        self.selected_id = None
        self.view.set_actions_enabled(False)

    def on_row_selected(self, _event):
        self.selected_id = self.view.get_selected_id()
        self.view.set_actions_enabled(self.selected_id is not None)

    def create_image_set(self):
        self._open_detail_window(existing=None)

    def edit_image_set(self):
        if self.selected_id is None:
            return
        image_set = self.db.get_image_set_by_id(self.selected_id)
        if image_set is None:
            return
        self._open_detail_window(existing=image_set)

    def copy_image_set(self):
        if self.selected_id is None:
            return

        source = self.db.get_image_set_by_id(self.selected_id)
        if source is None:
            return

        new_image_set = ImageSet(
            description=self._next_copy_name(source.description or "Image Set"),
            wells=source.wells,
            number_of_sites=source.number_of_sites,
            stack_size=source.stack_size,
            stack_step_size=source.stack_step_size,
            channel_1_number=source.channel_1_number,
            channel_1_intensity=source.channel_1_intensity,
            channel_2_number=source.channel_2_number,
            channel_2_intensity=source.channel_2_intensity,
        )
        self.db.add_image_set(new_image_set)
        self.refresh_view()

    def delete_image_set(self):
        if self.selected_id is None:
            return

        run_count = self.db.count_result_runs_for_image_set(self.selected_id)
        if run_count > 0:
            messagebox.showerror(
                "Delete Blocked",
                "This image set is referenced by existing result runs and cannot be deleted.",
            )
            return

        should_delete = messagebox.askyesno("Delete Image Set", "Delete selected image set?")
        if not should_delete:
            return

        self.db.delete_image_set(self.selected_id)
        self.refresh_view()

    def _open_detail_window(self, existing):
        is_edit = existing is not None
        detail_view = ImageSetDetailView(title="Edit Image Set" if is_edit else "New Image Set")

        initial_values = self._to_form_values(existing)
        detail_view.set_form_values(initial_values)
        initial_snapshot = deepcopy(detail_view.get_form_values())

        def on_save():
            form_values = detail_view.get_form_values()
            try:
                payload = self._validate_and_transform(form_values)
            except ValueError as exc:
                detail_view.show_error(str(exc))
                return

            if is_edit:
                image_set = self.db.get_image_set_by_id(existing.id)
                if image_set is None:
                    detail_view.show_error("Image set no longer exists.")
                    return
                for key, value in payload.items():
                    setattr(image_set, key, value)
                self.db.update_image_set(image_set)
            else:
                self.db.add_image_set(ImageSet(**payload))

            detail_view.root_window.destroy()
            self.refresh_view()

        def on_close():
            current_values = detail_view.get_form_values()
            if current_values != initial_snapshot and not detail_view.confirm_discard():
                return
            detail_view.root_window.destroy()

        detail_view.save_button.configure(command=on_save)
        detail_view.close_button.configure(command=on_close)
        detail_view.root_window.protocol("WM_DELETE_WINDOW", on_close)

    def _validate_and_transform(self, values):
        description = values["description"].strip()
        if not description:
            raise ValueError("Description cannot be blank.")

        wells = normalize_well_list(values["wells"])
        if len(wells) < 1:
            raise ValueError("Size of wells must be at least 1.")

        number_of_sites = self._parse_bounded_int(values["number_of_sites"], "Number of sites", 1, 9)
        stack_size = self._parse_bounded_int(values["stack_size"], "Stack size", 1, 99)
        stack_step_size = self._parse_bounded_int(values["stack_step_size"], "Step size", 1, 50)

        channel_1_number, channel_1_intensity = self._parse_led_pair(
            values["channel_1_number"],
            values["channel_1_intensity"],
            label="LED 1",
            required=True,
        )
        channel_2_number, channel_2_intensity = self._parse_led_pair(
            values["channel_2_number"],
            values["channel_2_intensity"],
            label="LED 2",
            required=False,
        )

        plates = self.db.get_all_plates()
        if not plates:
            raise ValueError("No plates available for geometry validation.")

        fits_any_plate = any(wells_fit_plate_geometry(wells, plate.num_rows, plate.num_cols) for plate in plates)
        if not fits_any_plate:
            raise ValueError("Wells are outside known plate geometries.")

        return {
            "description": description,
            "wells": serialize_well_list(wells),
            "number_of_sites": number_of_sites,
            "stack_size": stack_size,
            "stack_step_size": stack_step_size,
            "channel_1_number": channel_1_number,
            "channel_1_intensity": channel_1_intensity,
            "channel_2_number": channel_2_number,
            "channel_2_intensity": channel_2_intensity,
        }

    @staticmethod
    def _parse_bounded_int(raw_value, field_name, minimum, maximum):
        try:
            value = int(raw_value)
        except Exception as exc:
            raise ValueError(f"{field_name} must be an integer.") from exc

        if value < minimum or value > maximum:
            raise ValueError(f"{field_name} must be between {minimum} and {maximum} inclusive.")
        return value

    @staticmethod
    def _parse_led_pair(raw_channel, raw_intensity, label, required):
        has_channel = bool(raw_channel.strip())
        has_intensity = bool(raw_intensity.strip())

        if required and (not has_channel or not has_intensity):
            raise ValueError(f"{label} channel number and intensity are required.")

        if not required and not has_channel and not has_intensity:
            return None, None

        if has_channel != has_intensity:
            raise ValueError(f"{label} channel and intensity must be provided together.")

        try:
            channel = int(raw_channel)
        except Exception as exc:
            raise ValueError(f"{label} channel must be an integer.") from exc

        try:
            intensity = float(raw_intensity)
        except Exception as exc:
            raise ValueError(f"{label} intensity must be numeric.") from exc

        return channel, intensity

    @staticmethod
    def _to_form_values(existing):
        if existing is None:
            return {
                "description": "",
                "wells": "",
                "number_of_sites": "1",
                "stack_size": "1",
                "stack_step_size": "1",
                "channel_1_number": "",
                "channel_1_intensity": "",
                "channel_2_number": "",
                "channel_2_intensity": "",
            }

        return {
            "description": existing.description or "",
            "wells": existing.wells or "",
            "number_of_sites": "" if existing.number_of_sites is None else str(existing.number_of_sites),
            "stack_size": "" if existing.stack_size is None else str(existing.stack_size),
            "stack_step_size": "" if existing.stack_step_size is None else str(existing.stack_step_size),
            "channel_1_number": "" if existing.channel_1_number is None else str(existing.channel_1_number),
            "channel_1_intensity": "" if existing.channel_1_intensity is None else str(existing.channel_1_intensity),
            "channel_2_number": "" if existing.channel_2_number is None else str(existing.channel_2_number),
            "channel_2_intensity": "" if existing.channel_2_intensity is None else str(existing.channel_2_intensity),
        }

    @staticmethod
    def _next_copy_name(description):
        if description is None:
            description = "Image Set"

        pattern = r"^(.*) \(copy(?: (\d+))?\)$"
        match = re.match(pattern, description)
        if not match:
            return f"{description} (copy)"

        base = match.group(1)
        suffix_number = match.group(2)
        if suffix_number is None:
            return f"{base} (copy 2)"
        return f"{base} (copy {int(suffix_number) + 1})"
