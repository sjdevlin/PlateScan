import customtkinter
from PIL import Image


class ResultRunDetailView:
    def __init__(self):
        self.root_window = customtkinter.CTkToplevel()
        self.root_window.title("Result Viewer")
        self.root_window.geometry("1100x680")

        self.home_frame = customtkinter.CTkFrame(self.root_window)
        self.home_frame.pack(fill="both", expand=True)

        self.home_frame.grid_rowconfigure(0, weight=0)
        self.home_frame.grid_rowconfigure(1, weight=1)
        self.home_frame.grid_rowconfigure(2, weight=0)
        self.home_frame.grid_columnconfigure(0, weight=1)
        self.home_frame.grid_columnconfigure(1, weight=0)

        self.description_label = customtkinter.CTkLabel(self.home_frame, text="Metadata")
        self.description_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(10, 4))

        self.photo_frame = customtkinter.CTkFrame(self.home_frame, fg_color="transparent")
        self.photo_frame.grid(row=1, column=0, sticky="nsew", padx=(15, 10), pady=10)

        self.image_label = customtkinter.CTkLabel(
            self.photo_frame,
            width=760,
            height=520,
            text="",
            fg_color="#222222",
        )
        self.image_label.pack(expand=True, fill="both")

        self.side_button_frame = customtkinter.CTkFrame(self.home_frame, fg_color="transparent")
        self.side_button_frame.grid(row=1, column=1, sticky="ns", padx=(0, 15), pady=10)
        self.side_button_frame.grid_rowconfigure(0, weight=1)
        self.side_button_frame.grid_rowconfigure(1, weight=1)

        self.prev_stack_button = customtkinter.CTkButton(self.side_button_frame, text="Down in Stack")
        self.next_stack_button = customtkinter.CTkButton(self.side_button_frame, text="Up in Stack")
        self.prev_stack_button.grid(row=0, column=0, padx=5, pady=10, sticky="s")
        self.next_stack_button.grid(row=1, column=0, padx=5, pady=10, sticky="n")

        self.button_frame = customtkinter.CTkFrame(self.home_frame, fg_color="transparent")
        self.button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 12))

        for col in range(5):
            self.button_frame.grid_columnconfigure(col, weight=1)

        self.prev_sample_button = customtkinter.CTkButton(self.button_frame, text="Prev Well")
        self.next_sample_button = customtkinter.CTkButton(self.button_frame, text="Next Well")
        self.prev_site_button = customtkinter.CTkButton(self.button_frame, text="Prev Site")
        self.next_site_button = customtkinter.CTkButton(self.button_frame, text="Next Site")
        self.toggle_channel_button = customtkinter.CTkButton(self.button_frame, text="Channel: --")

        self.prev_sample_button.grid(row=0, column=0, padx=5, pady=8)
        self.next_sample_button.grid(row=0, column=1, padx=5, pady=8)
        self.prev_site_button.grid(row=0, column=2, padx=5, pady=8)
        self.next_site_button.grid(row=0, column=3, padx=5, pady=8)
        self.toggle_channel_button.grid(row=0, column=4, padx=5, pady=8)

    def update_channel_button(self, channel_label):
        self.toggle_channel_button.configure(text=f"Channel: {channel_label}")

    def set_channel_button_enabled(self, enabled):
        state = customtkinter.NORMAL if enabled else customtkinter.DISABLED
        self.toggle_channel_button.configure(state=state)

    def show_image(self, path_to_tiff, meta_data=None):
        try:
            if meta_data:
                self.description_label.configure(text=meta_data)

            image = Image.open(path_to_tiff)
            if image.mode != "RGB":
                image = image.convert("RGB")

            target_width, target_height = 760, 520
            scale = min(target_width / image.width, target_height / image.height)
            new_width = max(1, int(image.width * scale))
            new_height = max(1, int(image.height * scale))
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            ctk_image = customtkinter.CTkImage(light_image=image, dark_image=image, size=(new_width, new_height))
            self.image_label.configure(image=ctk_image, text="")
            self.image_label.image = ctk_image

        except Exception as exc:
            self.image_label.configure(image=None, text=f"Error loading image:\n{exc}")
