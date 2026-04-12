import customtkinter
from tkinter import messagebox

from services import index_to_row_label


class ImageSandboxView:
    def __init__(self):
        self.root = customtkinter.CTkToplevel()
        self.root.title("Image Sandbox")
        self.root.geometry("960x760")

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.home_frame = customtkinter.CTkFrame(self.root)
        self.home_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        self.home_frame.grid_rowconfigure(2, weight=1)
        self.home_frame.grid_columnconfigure(0, weight=1)

        self.header_label = customtkinter.CTkLabel(
            self.home_frame,
            text="Select plate and well, then Move and Image with manual settings",
            text_color="gray80",
        )
        self.header_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.top_frame = customtkinter.CTkFrame(self.home_frame, fg_color="transparent")
        self.top_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.top_frame.grid_columnconfigure(1, weight=1)

        self.plate_label = customtkinter.CTkLabel(self.top_frame, text="Plate")
        self.plate_label.grid(row=0, column=0, padx=(0, 8), pady=6, sticky="w")

        self.plate_var = customtkinter.StringVar(value="Select Plate")
        self.plate_menu = customtkinter.CTkOptionMenu(self.top_frame, variable=self.plate_var, values=["Select Plate"])
        self.plate_menu.grid(row=0, column=1, sticky="ew", pady=6)

        self.plate_frame = customtkinter.CTkFrame(self.home_frame)
        self.plate_frame.grid(row=2, column=0, sticky="nsew")
        self.plate_frame.grid_rowconfigure(0, weight=1)
        self.plate_frame.grid_columnconfigure(0, weight=1)

        self.controls_frame = customtkinter.CTkFrame(self.home_frame)
        self.controls_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))

        self.controls_frame.grid_columnconfigure(0, weight=0)
        self.controls_frame.grid_columnconfigure(1, weight=1)
        self.controls_frame.grid_columnconfigure(2, weight=0)
        self.controls_frame.grid_columnconfigure(3, weight=1)

        self.led_number_label = customtkinter.CTkLabel(self.controls_frame, text="LED number")
        self.led_number_entry = customtkinter.CTkEntry(self.controls_frame)

        self.led_intensity_label = customtkinter.CTkLabel(self.controls_frame, text="LED intensity")
        self.led_intensity_entry = customtkinter.CTkEntry(self.controls_frame)

        self.exposure_label = customtkinter.CTkLabel(self.controls_frame, text="Exposure time")
        self.exposure_entry = customtkinter.CTkEntry(self.controls_frame)

        self.autofocus_label = customtkinter.CTkLabel(self.controls_frame, text="Autofocus")
        self.autofocus_switch = customtkinter.CTkSwitch(self.controls_frame, text="Enabled")

        self.led_number_label.grid(row=0, column=0, padx=8, pady=6, sticky="w")
        self.led_number_entry.grid(row=0, column=1, padx=8, pady=6, sticky="ew")
        self.led_intensity_label.grid(row=0, column=2, padx=8, pady=6, sticky="w")
        self.led_intensity_entry.grid(row=0, column=3, padx=8, pady=6, sticky="ew")

        self.exposure_label.grid(row=1, column=0, padx=8, pady=6, sticky="w")
        self.exposure_entry.grid(row=1, column=1, padx=8, pady=6, sticky="ew")
        self.autofocus_label.grid(row=1, column=2, padx=8, pady=6, sticky="w")
        self.autofocus_switch.grid(row=1, column=3, padx=8, pady=6, sticky="w")

        self.buttons_frame = customtkinter.CTkFrame(self.home_frame, fg_color="transparent")
        self.buttons_frame.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        self.buttons_frame.grid_columnconfigure(0, weight=1)
        self.buttons_frame.grid_columnconfigure(1, weight=1)
        self.buttons_frame.grid_columnconfigure(2, weight=2)

        self.move_button = customtkinter.CTkButton(self.buttons_frame, text="Move", state=customtkinter.DISABLED)
        self.image_button = customtkinter.CTkButton(self.buttons_frame, text="Image", state=customtkinter.DISABLED)
        self.selection_label = customtkinter.CTkLabel(self.buttons_frame, text="No well selected")

        self.move_button.grid(row=0, column=0, padx=8, pady=8)
        self.image_button.grid(row=0, column=1, padx=8, pady=8)
        self.selection_label.grid(row=0, column=2, padx=8, pady=8, sticky="e")

        self.canvas = None
        self.well_lookup = {}

    def set_plate_options(self, options):
        if not options:
            options = ["No plates available"]
        self.plate_menu.configure(values=options)
        self.plate_var.set(options[0])

    def bind_plate_change(self, callback):
        self.plate_menu.configure(command=callback)

    def get_selected_plate_option(self):
        return self.plate_var.get()

    def set_default_controls(self, led_number, led_intensity, exposure_time, autofocus):
        self.led_number_entry.delete(0, "end")
        self.led_number_entry.insert(0, str(led_number))

        self.led_intensity_entry.delete(0, "end")
        self.led_intensity_entry.insert(0, str(led_intensity))

        self.exposure_entry.delete(0, "end")
        self.exposure_entry.insert(0, str(exposure_time))

        if autofocus:
            self.autofocus_switch.select()
        else:
            self.autofocus_switch.deselect()

    def set_selected_well(self, row_label, col_number):
        self.selection_label.configure(text=f"Selected: {row_label}{col_number}")

    def show_plate(self, plate, selected_well, click_callback):
        for widget in self.plate_frame.winfo_children():
            widget.destroy()

        scale = 5
        width = int((plate.outline_width or 127.8) * scale)
        height = int((plate.outline_length or 85.5) * scale)

        self.canvas = customtkinter.CTkCanvas(
            self.plate_frame,
            width=width,
            height=height,
            highlightthickness=0,
            bd=0,
            bg="#2a2a2a",
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.canvas.bind("<Button-1>", click_callback)

        self.canvas.create_rectangle(2, 2, width - 2, height - 2, outline="#888888", width=2)

        self.well_lookup = {}
        num_rows = int(plate.num_rows or 0)
        num_cols = int(plate.num_cols or 0)

        offset_x = float(plate.centre_first_well_offset_x or 0)
        offset_y = float(plate.centre_first_well_offset_y or 0)
        spacing_x = float(plate.well_spacing_x or 0)
        spacing_y = float(plate.well_spacing_y or 0)
        radius = max(3.0, float(plate.well_dimension or 2.0) )

        for row_idx in range(num_rows):
            row_label = index_to_row_label(row_idx)
            for col_idx in range(num_cols):
                col_num = col_idx + 1
                x = (offset_x + (col_idx * spacing_x)) * scale
                y = (offset_y + (row_idx * spacing_y)) * scale

                is_selected = selected_well == (row_label, col_num)
                fill = "#f5f5f5" if not is_selected else "#2dd4bf"
                outline = "#2dd4bf" if is_selected else ""

                well_item = self.canvas.create_oval(
                    x - radius,
                    y - radius,
                    x + radius,
                    y + radius,
                    fill=fill,
                    outline=outline,
                    width=2 if is_selected else 0,
                )
                self.well_lookup[well_item] = (row_label, col_num)

    def get_clicked_well(self, event):
        if self.canvas is None:
            return None
        clicked_item = self.canvas.find_closest(event.x, event.y)
        if not clicked_item:
            return None
        return self.well_lookup.get(clicked_item[0])

    def set_move_enabled(self, enabled):
        self.move_button.configure(state=customtkinter.NORMAL if enabled else customtkinter.DISABLED)

    def set_image_enabled(self, enabled):
        self.image_button.configure(state=customtkinter.NORMAL if enabled else customtkinter.DISABLED)

    def display_error(self, message):
        messagebox.showerror("Error", message)

    def display_info(self, message):
        messagebox.showinfo("Info", message)
