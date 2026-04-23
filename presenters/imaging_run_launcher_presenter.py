import threading
from tkinter import messagebox, simpledialog

from operators import ResultRunOperator
from services import Logger, normalize_well_list


class ImagingRunLauncherPresenter:
    def __init__(self, view, db):
        self.view = view
        self.db = db
        self.logger = Logger()

        self.selected_image_set_id = None
        self.selected_plate_id = None

        self.run_active = False
        self.current_operator = None
        self.current_thread = None
        self.current_stop_event = None
        self.dry_run = False

        self.view.bind_image_set_selection(self.on_image_set_selected)
        self.view.bind_plate_selection(self.on_plate_selected)
        self.view.run_button.configure(command=self.run_selected)
        self.view.stop_button.configure(command=self.stop_run)

        self.refresh_view()

    def refresh_view(self):
        image_sets = self.db.get_all_image_sets()
        image_set_rows = []
        for image_set in image_sets:
            well_count = self._count_wells_for_display(image_set)
            image_set_rows.append(
                (
                    image_set.id,
                    image_set.description,
                    well_count,
                    image_set.number_of_sites,
                    image_set.stack_size,
                    image_set.stack_step_size,
                    "On" if bool(getattr(image_set, "autofocus", False)) else "Off",
                )
            )
        self.view.list_image_sets(image_set_rows)

        plates = self.db.get_all_plates()
        plate_rows = [
            (
                plate.id,
                plate.description,
                int(plate.num_rows or 0) * int(plate.num_cols or 0),
            )
            for plate in plates
        ]
        self.view.list_plates(plate_rows)

        self.selected_image_set_id = None
        self.selected_plate_id = None
        self.dry_run = False
        self.view.set_run_enabled(False)

    def on_image_set_selected(self, _event):
        self.selected_image_set_id = self.view.get_selected_image_set_id()
        self._update_run_button_state()

    def on_plate_selected(self, _event):
        self.selected_plate_id = self.view.get_selected_plate_id()
        self._update_run_button_state()

    def _update_run_button_state(self):
        should_enable = (
            (self.selected_image_set_id is not None)
            and (self.selected_plate_id is not None)
            and (not self.run_active)
        )
        self.view.set_run_enabled(should_enable)

    def run_selected(self):
        if self.run_active:
            return

        image_set = self.db.get_image_set_by_id(self.selected_image_set_id)
        plate = self.db.get_plate_by_id(self.selected_plate_id)
        if image_set is None or plate is None:
            messagebox.showerror("Run Error", "Please select a valid image set and plate.")
            return

        run_description = simpledialog.askstring("Result Run Description", "Enter description for this run:")
        if run_description is None:
            return

        run_description = run_description.strip()
        if not run_description:
            messagebox.showerror("Run Error", "Description cannot be blank.")
            return

        messagebox.showinfo("Check Origin", "Please confirm the X and Y co-ordinates are reset to origin.")
        if bool(getattr(image_set, "autofocus", False)):
            messagebox.showinfo(
                "Autofocus Enabled",
                "Autofocus is enabled for this image set. Please confirm focus is locked before starting the run.",
            )

        stop_event = threading.Event()

        def handle_operator_error(source, error_message):
            if stop_event is not None:
                stop_event.set()
            self.view.root_window.after(
                0,
                lambda: messagebox.showerror("Run Error", f"{source.capitalize()} error:\n{error_message}"),
            )

        try:
            operator = ResultRunOperator(
                plate=plate,
                image_set=image_set,
                run_description=run_description,
                db=self.db,
                stop_event=stop_event,
                error_callback=handle_operator_error,
            )
        except Exception as exc:
            messagebox.showerror("Run Error", str(exc))
            return

        try:
            first_well = operator.move_to_first_site_for_focus_check()
            messagebox.showinfo(
                "Focus Check",
                f"The microscope has moved to the first well ({first_well}). "
                "Adjust the image into focus, then press OK to start the run.",
            )
            operator.capture_focus_position()
        except Exception as exc:
            messagebox.showerror("Run Error", f"Failed to prepare the first well for focus check:\n{exc}")
            return

        run_thread = threading.Thread(target=operator.run, daemon=False)
        self.dry_run = bool(getattr(operator, "dry_run", False))

        self.run_active = True
        self.current_operator = operator
        self.current_thread = run_thread
        self.current_stop_event = stop_event

        self.view.set_status("Running (Dry Run)" if self.dry_run else "Running")
        self.view.set_run_enabled(False)
        self.view.set_stop_enabled(True)

        run_thread.start()

        monitor_thread = threading.Thread(target=self._monitor_run_completion, args=(run_thread,), daemon=True)
        monitor_thread.start()

    def stop_run(self):
        if not self.run_active:
            return

        if not messagebox.askyesno("Stop Run", "Stop/cancel the current run?"):
            return

        if self.current_operator is not None:
            self.current_operator.request_stop("Run stop requested from UI")

        if self.current_stop_event is not None:
            self.current_stop_event.set()

        self.view.set_status("Stopping (Dry Run)" if self.dry_run else "Stopping")
        self.view.set_stop_enabled(False)

    def _monitor_run_completion(self, run_thread):
        run_thread.join()
        self.view.root_window.after(0, self._on_run_finished)

    def _on_run_finished(self):
        self.run_active = False
        self.current_operator = None
        self.current_thread = None
        self.current_stop_event = None
        self.dry_run = False

        self.view.set_status("Idle")
        self.view.set_stop_enabled(False)
        self._update_run_button_state()

    def _count_wells_for_display(self, image_set):
        raw_wells = image_set.wells or ""
        if not raw_wells.strip():
            return 0

        try:
            return len(normalize_well_list(raw_wells))
        except Exception as exc:
            raw_count = len([part for part in raw_wells.split(",") if part.strip()])
            self.logger.warning(
                f"Image set {image_set.id} has invalid well definitions; displaying raw count instead: {exc}"
            )
            return raw_count
