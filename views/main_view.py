import customtkinter


class MainView:
    def __init__(self, root_window):
        self.root_window = root_window

        self.home_frame = customtkinter.CTkFrame(self.root_window, fg_color="transparent")
        self.home_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.home_frame.grid_columnconfigure(0, weight=1)

        self.title_label = customtkinter.CTkLabel(
            self.home_frame,
            text="PlateScan",
            font=customtkinter.CTkFont(size=24, weight="bold"),
        )
        self.subtitle_label = customtkinter.CTkLabel(
            self.home_frame,
            text="Automated multiwell imaging",
            text_color="gray80",
        )

        self.manage_image_sets_button = customtkinter.CTkButton(
            self.home_frame,
            text="Manage Image Sets",
            state=customtkinter.NORMAL,
        )
        self.launch_imaging_run_button = customtkinter.CTkButton(
            self.home_frame,
            text="Launch Imaging Run",
            state=customtkinter.NORMAL,
        )
        self.review_results_button = customtkinter.CTkButton(
            self.home_frame,
            text="Review Results",
            state=customtkinter.NORMAL,
        )
        self.image_sandbox_button = customtkinter.CTkButton(
            self.home_frame,
            text="Image Sandbox",
            state=customtkinter.NORMAL,
        )

        self.title_label.grid(row=0, column=0, pady=(8, 2))
        self.subtitle_label.grid(row=1, column=0, pady=(0, 18))

        self.manage_image_sets_button.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        self.launch_imaging_run_button.grid(row=3, column=0, sticky="ew", padx=20, pady=10)
        self.review_results_button.grid(row=4, column=0, sticky="ew", padx=20, pady=10)
        self.image_sandbox_button.grid(row=5, column=0, sticky="ew", padx=20, pady=10)
