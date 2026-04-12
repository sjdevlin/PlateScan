import customtkinter
from tkinter import ttk


class ImageSetManagerView:
    def __init__(self):
        self.root_window = customtkinter.CTkToplevel()
        self.root_window.title("Manage Image Sets")
        self.root_window.geometry("1100x620")

        self.home_frame = customtkinter.CTkFrame(self.root_window)
        self.home_frame.pack(fill="both", expand=True)
        self.home_frame.grid_rowconfigure(0, weight=0)
        self.home_frame.grid_rowconfigure(1, weight=1)
        self.home_frame.grid_rowconfigure(2, weight=0)
        self.home_frame.grid_columnconfigure(0, weight=1)

        self.header_label = customtkinter.CTkLabel(
            self.home_frame,
            text="Create, edit, copy, and delete image set definitions",
            text_color="gray80",
        )
        self.header_label.grid(row=0, column=0, sticky="w", padx=20, pady=(14, 0))

        self.table_frame = customtkinter.CTkFrame(self.home_frame, fg_color="transparent")
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=12)
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

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

        self.columns = ("id", "description", "sites", "stack_size", "stack_step", "led_1", "led_2")
        self.table = ttk.Treeview(self.table_frame, columns=self.columns, show="headings")

        self.table.heading("id", text="ID")
        self.table.heading("description", text="Description")
        self.table.heading("sites", text="Number of Sites")
        self.table.heading("stack_size", text="Stack Size")
        self.table.heading("stack_step", text="Stack Step")
        self.table.heading("led_1", text="LED 1")
        self.table.heading("led_2", text="LED 2")

        self.table.column("id", width=60, anchor="w", stretch=False)
        self.table.column("description", width=450, anchor="w")
        self.table.column("sites", width=120, anchor="w", stretch=False)
        self.table.column("stack_size", width=100, anchor="w", stretch=False)
        self.table.column("stack_step", width=100, anchor="w", stretch=False)
        self.table.column("led_1", width=80, anchor="w", stretch=False)
        self.table.column("led_2", width=80, anchor="w", stretch=False)

        self.table.grid(row=0, column=0, sticky="nsew")

        self.button_frame = customtkinter.CTkFrame(self.home_frame, fg_color="transparent")
        self.button_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))

        for col in range(4):
            self.button_frame.grid_columnconfigure(col, weight=1)

        self.edit_button = customtkinter.CTkButton(self.button_frame, text="Edit", state=customtkinter.DISABLED)
        self.copy_button = customtkinter.CTkButton(self.button_frame, text="Copy", state=customtkinter.DISABLED)
        self.delete_button = customtkinter.CTkButton(self.button_frame, text="Delete", state=customtkinter.DISABLED)
        self.new_button = customtkinter.CTkButton(self.button_frame, text="New", state=customtkinter.NORMAL)

        self.edit_button.grid(row=0, column=0, padx=10, pady=10)
        self.copy_button.grid(row=0, column=1, padx=10, pady=10)
        self.delete_button.grid(row=0, column=2, padx=10, pady=10)
        self.new_button.grid(row=0, column=3, padx=10, pady=10)

    def bind_row_selection(self, callback):
        self.table.bind("<<TreeviewSelect>>", callback)

    def list_image_sets(self, rows):
        self.table.delete(*self.table.get_children())
        for row in rows:
            self.table.insert("", "end", values=row)

    def get_selected_id(self):
        selected_item = self.table.selection()
        if not selected_item:
            return None
        return int(self.table.item(selected_item[0], "values")[0])

    def set_actions_enabled(self, enabled):
        state = customtkinter.NORMAL if enabled else customtkinter.DISABLED
        self.edit_button.configure(state=state)
        self.copy_button.configure(state=state)
        self.delete_button.configure(state=state)
