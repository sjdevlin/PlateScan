import customtkinter
from tkinter import ttk


class ResultRunListView:
    def __init__(self):
        self.root_window = customtkinter.CTkToplevel()
        self.root_window.title("Review Results")
        self.root_window.geometry("1100x620")

        self.home_frame = customtkinter.CTkFrame(self.root_window)
        self.home_frame.pack(fill="both", expand=True)

        self.home_frame.grid_rowconfigure(0, weight=0)
        self.home_frame.grid_rowconfigure(1, weight=1)
        self.home_frame.grid_rowconfigure(2, weight=0)
        self.home_frame.grid_columnconfigure(0, weight=1)

        self.header_label = customtkinter.CTkLabel(
            self.home_frame,
            text="Select a result run to inspect captured image stacks",
            text_color="gray80",
        )
        self.header_label.grid(row=0, column=0, sticky="w", padx=20, pady=(14, 0))

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

        self.table_frame = customtkinter.CTkFrame(self.home_frame, fg_color="transparent")
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=12)
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        self.res_columns = ("id", "description", "date", "image_set", "plate")
        self.res_table = ttk.Treeview(self.table_frame, columns=self.res_columns, show="headings")

        self.res_table.heading("id", text="ID")
        self.res_table.heading("description", text="Result Run")
        self.res_table.heading("date", text="Date")
        self.res_table.heading("image_set", text="Image Set")
        self.res_table.heading("plate", text="Plate")

        self.res_table.column("id", width=60, anchor="w", stretch=False)
        self.res_table.column("description", width=350, anchor="w")
        self.res_table.column("date", width=150, anchor="w", stretch=False)
        self.res_table.column("image_set", width=250, anchor="w")
        self.res_table.column("plate", width=250, anchor="w")

        self.res_table.grid(row=0, column=0, sticky="nsew")

        self.button_frame = customtkinter.CTkFrame(self.home_frame, fg_color="transparent")
        self.button_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.button_frame.grid_columnconfigure(0, weight=1)

        self.review_button = customtkinter.CTkButton(
            self.button_frame,
            text="Review",
            state=customtkinter.DISABLED,
        )
        self.review_button.grid(row=0, column=0, padx=10, pady=10)

    def list_results(self, data):
        self.res_table.delete(*self.res_table.get_children())
        for row in data:
            self.res_table.insert("", "end", values=row)

    def res_bind_row_selection(self, callback):
        self.res_table.bind("<<TreeviewSelect>>", callback)

    def get_id_of_selected_res_row(self):
        selected_item = self.res_table.selection()
        if selected_item:
            return int(self.res_table.item(selected_item[0], "values")[0])
        return None

    def enable_review_button(self):
        self.review_button.configure(state=customtkinter.NORMAL)

    def disable_review_button(self):
        self.review_button.configure(state=customtkinter.DISABLED)
