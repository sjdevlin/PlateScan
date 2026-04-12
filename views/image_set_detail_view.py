import customtkinter
from tkinter import messagebox


class ImageSetDetailView:
    def __init__(self, title="Image Set Detail"):
        self.root_window = customtkinter.CTkToplevel()
        self.root_window.title(title)
        self.root_window.geometry("680x600")

        self.home_frame = customtkinter.CTkFrame(self.root_window)
        self.home_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.home_frame.grid_columnconfigure(0, weight=0)
        self.home_frame.grid_columnconfigure(1, weight=1)

        self.header_label = customtkinter.CTkLabel(
            self.home_frame,
            text="Define imaging sites, stack settings, channels, and wells",
            text_color="gray80",
        )
        self.header_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        labels = [
            "Description",
            "Wells (comma separated)",
            "Number of Sites (1-9)",
            "Stack Size (1-99)",
            "Stack Step (1-50 um)",
            "LED 1 Channel",
            "LED 1 Intensity",
            "LED 2 Channel (optional)",
            "LED 2 Intensity (optional)",
        ]

        self.entries = {}
        keys = [
            "description",
            "wells",
            "number_of_sites",
            "stack_size",
            "stack_step_size",
            "channel_1_number",
            "channel_1_intensity",
            "channel_2_number",
            "channel_2_intensity",
        ]

        row_offset = 1
        for row_index, (label_text, key) in enumerate(zip(labels, keys)):
            label = customtkinter.CTkLabel(self.home_frame, text=label_text)
            label.grid(row=row_index + row_offset, column=0, sticky="w", padx=(0, 10), pady=8)

            entry = customtkinter.CTkEntry(self.home_frame, width=380)
            entry.grid(row=row_index + row_offset, column=1, sticky="ew", pady=8)
            self.entries[key] = entry

        self.button_frame = customtkinter.CTkFrame(self.home_frame, fg_color="transparent")
        self.button_frame.grid(row=len(labels) + row_offset, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)

        self.save_button = customtkinter.CTkButton(self.button_frame, text="Save")
        self.close_button = customtkinter.CTkButton(self.button_frame, text="Close")
        self.save_button.grid(row=0, column=0, padx=8, pady=8)
        self.close_button.grid(row=0, column=1, padx=8, pady=8)

    def set_form_values(self, values):
        for key, entry in self.entries.items():
            entry.delete(0, "end")
            value = values.get(key, "")
            if value is None:
                value = ""
            entry.insert(0, str(value))

    def get_form_values(self):
        return {key: entry.get().strip() for key, entry in self.entries.items()}

    def confirm_discard(self):
        return messagebox.askyesno("Discard Changes", "Discard unsaved changes?")

    def show_error(self, message):
        messagebox.showerror("Validation Error", message)
