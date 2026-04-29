import customtkinter
from tkinter import ttk


class ImagingRunProgressWindow:
    def __init__(self, parent):
        self.root_window = customtkinter.CTkToplevel(parent)
        self.root_window.title("Imaging Run Progress")
        self.root_window.geometry("520x320")
        self.root_window.grid_columnconfigure(0, weight=1)
        self.root_window.grid_rowconfigure(1, weight=1)

        self.header_label = customtkinter.CTkLabel(
            self.root_window,
            text="Imaging Run In Progress",
            font=customtkinter.CTkFont(size=18, weight="bold"),
        )
        self.header_label.grid(row=0, column=0, padx=20, pady=(18, 10), sticky="w")

        self.body_frame = customtkinter.CTkFrame(self.root_window)
        self.body_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.body_frame.grid_columnconfigure(0, weight=1)

        self.status_label = customtkinter.CTkLabel(self.body_frame, text="Status: Idle", anchor="w")
        self.phase_label = customtkinter.CTkLabel(self.body_frame, text="Phase: --", anchor="w")
        self.location_label = customtkinter.CTkLabel(self.body_frame, text="Well/Site: --", anchor="w")
        self.stack_label = customtkinter.CTkLabel(self.body_frame, text="Stack/Channel: --", anchor="w")
        self.site_count_label = customtkinter.CTkLabel(self.body_frame, text="Sites: 0 / 0", anchor="w")
        self.frame_count_label = customtkinter.CTkLabel(self.body_frame, text="Frames: 0 / 0", anchor="w")
        self.progress_bar = customtkinter.CTkProgressBar(self.body_frame)
        self.progress_bar.set(0)

        self.status_label.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        self.phase_label.grid(row=1, column=0, padx=16, pady=8, sticky="ew")
        self.location_label.grid(row=2, column=0, padx=16, pady=8, sticky="ew")
        self.stack_label.grid(row=3, column=0, padx=16, pady=8, sticky="ew")
        self.site_count_label.grid(row=4, column=0, padx=16, pady=8, sticky="ew")
        self.frame_count_label.grid(row=5, column=0, padx=16, pady=8, sticky="ew")
        self.progress_bar.grid(row=6, column=0, padx=16, pady=(12, 16), sticky="ew")

        self.button_frame = customtkinter.CTkFrame(self.root_window, fg_color="transparent")
        self.button_frame.grid(row=2, column=0, padx=20, pady=(0, 18), sticky="ew")
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)

        self.pause_button = customtkinter.CTkButton(
            self.button_frame,
            text="Pause",
            fg_color="#995c00",
        )
        self.cancel_button = customtkinter.CTkButton(
            self.button_frame,
            text="Cancel Run",
            fg_color="#8b1a1a",
        )

        self.pause_button.grid(row=0, column=0, padx=(0, 8), pady=8, sticky="ew")
        self.cancel_button.grid(row=0, column=1, padx=(8, 0), pady=8, sticky="ew")
        self.root_window.protocol("WM_DELETE_WINDOW", self.root_window.lift)

    def set_status(self, text):
        self.status_label.configure(text=f"Status: {text}")

    def set_phase(self, text):
        self.phase_label.configure(text=f"Phase: {text or '--'}")

    def set_location(self, well, site_number):
        if well is None or site_number is None:
            text = "Well/Site: --"
        else:
            text = f"Well/Site: {well} / Site {site_number + 1}"
        self.location_label.configure(text=text)

    def set_stack_channel(self, stack_index, channel_number):
        if stack_index is None and channel_number is None:
            text = "Stack/Channel: --"
        else:
            stack_text = "--" if stack_index is None else str(stack_index + 1)
            channel_text = "--" if channel_number is None else str(channel_number)
            text = f"Stack/Channel: {stack_text} / {channel_text}"
        self.stack_label.configure(text=text)

    def set_site_counts(self, completed, total):
        self.site_count_label.configure(text=f"Sites: {completed} / {total}")

    def set_frame_counts(self, completed, total):
        self.frame_count_label.configure(text=f"Frames: {completed} / {total}")

    def set_progress(self, completed, total):
        ratio = 0 if total <= 0 else max(0.0, min(1.0, completed / total))
        self.progress_bar.set(ratio)

    def set_pause_text(self, text):
        self.pause_button.configure(text=text)

    def set_pause_enabled(self, enabled):
        self.pause_button.configure(state=customtkinter.NORMAL if enabled else customtkinter.DISABLED)

    def set_cancel_enabled(self, enabled):
        self.cancel_button.configure(state=customtkinter.NORMAL if enabled else customtkinter.DISABLED)

    def bind_pause(self, callback):
        self.pause_button.configure(command=callback)

    def bind_cancel(self, callback):
        self.cancel_button.configure(command=callback)

    def bind_close(self, callback):
        self.root_window.protocol("WM_DELETE_WINDOW", callback)

    def close(self):
        if self.root_window.winfo_exists():
            self.root_window.destroy()


class ImagingRunLauncherView:
    def __init__(self):
        self.root_window = customtkinter.CTkToplevel()
        self.root_window.title("Launch Imaging Run")
        self.root_window.geometry("1180x760")

        self.home_frame = customtkinter.CTkFrame(self.root_window)
        self.home_frame.pack(fill="both", expand=True)

        self.home_frame.grid_rowconfigure(0, weight=0)
        self.home_frame.grid_rowconfigure(1, weight=1)
        self.home_frame.grid_rowconfigure(2, weight=1)
        self.home_frame.grid_rowconfigure(3, weight=0)
        self.home_frame.grid_columnconfigure(0, weight=1)

        self.header_label = customtkinter.CTkLabel(
            self.home_frame,
            text="Select one image set and one plate, then launch an imaging run",
            text_color="gray80",
        )
        self.header_label.grid(row=0, column=0, sticky="w", padx=20, pady=(12, 0))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="gray",
            fieldbackground="black",
            foreground="gray85",
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            anchor="w",
            background="black",
            foreground="gray99",
            borderwidth=0,
            font=("Arial", 10, "bold"),
        )

        self.image_set_frame = customtkinter.CTkFrame(self.home_frame, fg_color="transparent")
        self.image_set_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 10))
        self.image_set_frame.grid_rowconfigure(1, weight=1)
        self.image_set_frame.grid_columnconfigure(0, weight=1)

        image_set_label = customtkinter.CTkLabel(self.image_set_frame, text="Image Sets")
        image_set_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.image_set_columns = ("id", "description", "wells", "sites", "stack", "step", "autofocus")
        self.image_set_table = ttk.Treeview(self.image_set_frame, columns=self.image_set_columns, show="headings")
        self.image_set_table.heading("id", text="ID")
        self.image_set_table.heading("description", text="Description")
        self.image_set_table.heading("wells", text="Wells")
        self.image_set_table.heading("sites", text="Sites")
        self.image_set_table.heading("stack", text="Stack Size")
        self.image_set_table.heading("step", text="Step")
        self.image_set_table.heading("autofocus", text="Autofocus")

        self.image_set_table.column("id", width=60, anchor="w", stretch=False)
        self.image_set_table.column("description", width=520, anchor="w")
        self.image_set_table.column("wells", width=80, anchor="w", stretch=False)
        self.image_set_table.column("sites", width=80, anchor="w", stretch=False)
        self.image_set_table.column("stack", width=100, anchor="w", stretch=False)
        self.image_set_table.column("step", width=100, anchor="w", stretch=False)
        self.image_set_table.column("autofocus", width=100, anchor="w", stretch=False)
        self.image_set_table.grid(row=1, column=0, sticky="nsew")

        self.plate_frame = customtkinter.CTkFrame(self.home_frame, fg_color="transparent")
        self.plate_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 10))
        self.plate_frame.grid_rowconfigure(1, weight=1)
        self.plate_frame.grid_columnconfigure(0, weight=1)

        plate_label = customtkinter.CTkLabel(self.plate_frame, text="Plates")
        plate_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.plate_columns = ("id", "description", "num_wells")
        self.plate_table = ttk.Treeview(self.plate_frame, columns=self.plate_columns, show="headings")
        self.plate_table.heading("id", text="ID")
        self.plate_table.heading("description", text="Description")
        self.plate_table.heading("num_wells", text="Number of Wells")

        self.plate_table.column("id", width=60, anchor="w", stretch=False)
        self.plate_table.column("description", width=760, anchor="w")
        self.plate_table.column("num_wells", width=160, anchor="w", stretch=False)
        self.plate_table.grid(row=1, column=0, sticky="nsew")

        self.button_frame = customtkinter.CTkFrame(self.home_frame, fg_color="transparent")
        self.button_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(6, 20))
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)
        self.button_frame.grid_columnconfigure(2, weight=2)

        self.run_button = customtkinter.CTkButton(self.button_frame, text="Run", state=customtkinter.DISABLED, fg_color="#992200")
        self.stop_button = customtkinter.CTkButton(
            self.button_frame,
            text="Stop / Cancel",
            state=customtkinter.DISABLED,
            fg_color="#8b1a1a",
        )
        self.status_label = customtkinter.CTkLabel(self.button_frame, text="Idle")

        self.run_button.grid(row=0, column=0, padx=10, pady=8)
        self.stop_button.grid(row=0, column=1, padx=10, pady=8)
        self.status_label.grid(row=0, column=2, padx=10, pady=8, sticky="e")
        self.progress_window = None

    def bind_image_set_selection(self, callback):
        self.image_set_table.bind("<<TreeviewSelect>>", callback)

    def bind_plate_selection(self, callback):
        self.plate_table.bind("<<TreeviewSelect>>", callback)

    def list_image_sets(self, rows):
        self.image_set_table.delete(*self.image_set_table.get_children())
        for row in rows:
            self.image_set_table.insert("", "end", values=row)

    def list_plates(self, rows):
        self.plate_table.delete(*self.plate_table.get_children())
        for row in rows:
            self.plate_table.insert("", "end", values=row)

    def get_selected_image_set_id(self):
        selected_item = self.image_set_table.selection()
        if not selected_item:
            return None
        return int(self.image_set_table.item(selected_item[0], "values")[0])

    def get_selected_plate_id(self):
        selected_item = self.plate_table.selection()
        if not selected_item:
            return None
        return int(self.plate_table.item(selected_item[0], "values")[0])

    def set_run_enabled(self, enabled):
        self.run_button.configure(state=customtkinter.NORMAL if enabled else customtkinter.DISABLED)

    def set_stop_enabled(self, enabled):
        self.stop_button.configure(state=customtkinter.NORMAL if enabled else customtkinter.DISABLED)

    def set_status(self, text):
        self.status_label.configure(text=text)

    def open_progress_window(self):
        if self.progress_window is not None and self.progress_window.root_window.winfo_exists():
            self.progress_window.root_window.lift()
            self.progress_window.root_window.focus()
            return self.progress_window
        self.progress_window = ImagingRunProgressWindow(self.root_window)
        return self.progress_window

    def close_progress_window(self):
        if self.progress_window is not None:
            self.progress_window.close()
            self.progress_window = None
