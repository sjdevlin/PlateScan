import customtkinter
from tkinter import ttk


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

        self.image_set_columns = ("id", "description", "wells", "sites", "stack", "step")
        self.image_set_table = ttk.Treeview(self.image_set_frame, columns=self.image_set_columns, show="headings")
        self.image_set_table.heading("id", text="ID")
        self.image_set_table.heading("description", text="Description")
        self.image_set_table.heading("wells", text="Wells")
        self.image_set_table.heading("sites", text="Sites")
        self.image_set_table.heading("stack", text="Stack Size")
        self.image_set_table.heading("step", text="Step")

        self.image_set_table.column("id", width=60, anchor="w", stretch=False)
        self.image_set_table.column("description", width=600, anchor="w")
        self.image_set_table.column("wells", width=80, anchor="w", stretch=False)
        self.image_set_table.column("sites", width=80, anchor="w", stretch=False)
        self.image_set_table.column("stack", width=100, anchor="w", stretch=False)
        self.image_set_table.column("step", width=100, anchor="w", stretch=False)
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
