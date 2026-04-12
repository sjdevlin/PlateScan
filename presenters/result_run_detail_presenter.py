from services import AppConfig, Logger, row_label_to_index


class ResultRunDetailPresenter:
    def __init__(self, result_run_id, view, db):
        self.view = view
        self.db = db
        self.app_config = AppConfig()
        self.logger = Logger()

        self.view.next_sample_button.configure(command=self.next_well)
        self.view.prev_sample_button.configure(command=self.prev_well)
        self.view.next_stack_button.configure(command=self.next_stack)
        self.view.prev_stack_button.configure(command=self.prev_stack)
        self.view.next_site_button.configure(command=self.next_site)
        self.view.prev_site_button.configure(command=self.prev_site)
        self.view.toggle_channel_button.configure(command=self.toggle_channel)

        result_run = self.db.get_result_run_by_id(result_run_id)
        self.image_set = self.db.get_image_set_by_id(result_run.image_set_id) if result_run else None

        self.preferred_channel_order = []
        if self.image_set is not None:
            for channel_number in [self.image_set.channel_1_number, self.image_set.channel_2_number]:
                if channel_number is not None and channel_number not in self.preferred_channel_order:
                    self.preferred_channel_order.append(channel_number)

        self.images = self.db.get_images_by_result_run_id(result_run_id)
        if not self.images:
            self.logger.error(f"No images found for result run {result_run_id}.")
            return

        self.well_keys = self._sorted_well_keys()
        self.well_index = 0
        self.site_number = self._initial_site_for_well(self.current_well_key)
        self.channel_number = None
        self.stack_index = 0
        self.stack_number = 0

        self._ensure_valid_selection(reset_stack=True)
        self.refresh_view()

    @property
    def current_well_key(self):
        return self.well_keys[self.well_index]

    def _sorted_well_keys(self):
        keys = {(img.well_row, int(img.well_column)) for img in self.images}
        return sorted(keys, key=lambda key: (row_label_to_index(key[0]), key[1]))

    def _images_for_current_selection(self):
        row, col = self.current_well_key
        return [
            image
            for image in self.images
            if image.well_row == row and int(image.well_column) == int(col) and image.site_number == self.site_number
        ]

    def _available_channels_for_selection(self):
        selection_images = sorted(self._images_for_current_selection(), key=lambda img: img.stack_number)
        detected_channels = []
        for image in selection_images:
            if image.led_number not in detected_channels:
                detected_channels.append(image.led_number)

        ordered_channels = [channel for channel in self.preferred_channel_order if channel in detected_channels]
        for channel in detected_channels:
            if channel not in ordered_channels:
                ordered_channels.append(channel)
        return ordered_channels

    def _channel_images(self, channel_number):
        return sorted(
            [image for image in self._images_for_current_selection() if image.led_number == channel_number],
            key=lambda image: image.stack_number,
        )

    def _ensure_valid_selection(self, reset_stack=False):
        self.channel_numbers = self._available_channels_for_selection()
        if not self.channel_numbers:
            self.channel_numbers = [None]

        if self.channel_number not in self.channel_numbers:
            self.channel_number = self.channel_numbers[0]
            reset_stack = True

        current_channel_images = self._channel_images(self.channel_number)
        if not current_channel_images:
            self.stack_index = 0
            self.stack_number = 0
            return

        if reset_stack:
            self.stack_index = self._get_index_of_sharpest_image(current_channel_images)
            self.stack_number = current_channel_images[self.stack_index].stack_number
            return

        target_stack = self.stack_number
        if target_stack is None:
            target_stack = current_channel_images[0].stack_number

        matching_index = next(
            (idx for idx, image in enumerate(current_channel_images) if image.stack_number == target_stack),
            None,
        )
        if matching_index is None:
            matching_index = 0

        self.stack_index = matching_index
        self.stack_number = current_channel_images[self.stack_index].stack_number

    def _get_index_of_sharpest_image(self, channel_images=None):
        if channel_images is None:
            channel_images = self._channel_images(self.channel_number)

        if not channel_images:
            return 0

        return max(
            range(len(channel_images)),
            key=lambda idx: channel_images[idx].focus_score if channel_images[idx].focus_score is not None else -1,
        )

    def _site_numbers_for_current_well(self):
        row, col = self.current_well_key
        site_numbers = {
            image.site_number for image in self.images if image.well_row == row and int(image.well_column) == int(col)
        }
        return sorted(site_numbers)

    def _initial_site_for_well(self, well_key):
        row, col = well_key
        site_numbers = sorted(
            {
                image.site_number
                for image in self.images
                if image.well_row == row and int(image.well_column) == int(col)
            }
        )
        return site_numbers[0] if site_numbers else 0

    def refresh_view(self):
        self._ensure_valid_selection()

        current_channel_images = self._channel_images(self.channel_number)
        selected_image = current_channel_images[self.stack_index] if current_channel_images else None
        if selected_image is not None:
            self.stack_number = selected_image.stack_number

        channel_index = self.channel_numbers.index(self.channel_number) if self.channel_number in self.channel_numbers else 0
        channel_label = str(channel_index + 1)
        if self.channel_number is not None:
            channel_label = f"{channel_label} (#{self.channel_number})"

        self.view.update_channel_button(channel_label)
        self.view.set_channel_button_enabled(len(self.channel_numbers) > 1)

        row, col = self.current_well_key
        stack_label = selected_image.stack_number if selected_image is not None else self.stack_number

        metadata = f"Well: {row}{col}"
        metadata += f"\nSite: {self.site_number}, Stack: {stack_label}"
        metadata += f"\nChannel: {channel_label}"

        if selected_image is None:
            self.logger.warning(
                f"No image found for well {row}{col}, site {self.site_number}, stack {self.stack_number}, channel {self.channel_number}."
            )
            self._update_nav_buttons(current_channel_images)
            return

        if selected_image.focus_score is not None:
            metadata += f"\nFocus Score: {selected_image.focus_score:.2f}"
        else:
            metadata += "\nFocus Score: n/a"

        self._update_nav_buttons(current_channel_images)

        image_file_path = selected_image.file_path
        base_path = self.app_config.get("image_file_directory", "")
        full_image_path = f"{base_path}/{image_file_path}" if base_path else image_file_path
        self.view.show_image(full_image_path, metadata)

    def next_well(self):
        if self.well_index < len(self.well_keys) - 1:
            self.well_index += 1
            self.site_number = self._initial_site_for_well(self.current_well_key)
            self._ensure_valid_selection(reset_stack=True)
            self.refresh_view()

    def prev_well(self):
        if self.well_index > 0:
            self.well_index -= 1
            self.site_number = self._initial_site_for_well(self.current_well_key)
            self._ensure_valid_selection(reset_stack=True)
            self.refresh_view()

    def next_site(self):
        sites = self._site_numbers_for_current_well()
        if not sites:
            return
        try:
            current_index = sites.index(self.site_number)
        except ValueError:
            current_index = 0

        if current_index < len(sites) - 1:
            self.site_number = sites[current_index + 1]
            self._ensure_valid_selection(reset_stack=True)
            self.refresh_view()

    def prev_site(self):
        sites = self._site_numbers_for_current_well()
        if not sites:
            return
        try:
            current_index = sites.index(self.site_number)
        except ValueError:
            current_index = 0

        if current_index > 0:
            self.site_number = sites[current_index - 1]
            self._ensure_valid_selection(reset_stack=True)
            self.refresh_view()

    def next_stack(self):
        channel_images = self._channel_images(self.channel_number)
        if self.stack_index < len(channel_images) - 1:
            self.stack_index += 1
            self.stack_number = channel_images[self.stack_index].stack_number
        self.refresh_view()

    def prev_stack(self):
        if self.stack_index > 0:
            self.stack_index -= 1
            channel_images = self._channel_images(self.channel_number)
            if channel_images:
                self.stack_number = channel_images[self.stack_index].stack_number
        self.refresh_view()

    def toggle_channel(self):
        if len(self.channel_numbers) <= 1:
            return

        current_channel_images = self._channel_images(self.channel_number)
        if current_channel_images:
            self.stack_number = current_channel_images[self.stack_index].stack_number

        current_index = self.channel_numbers.index(self.channel_number)
        self.channel_number = self.channel_numbers[(current_index + 1) % len(self.channel_numbers)]
        self._ensure_valid_selection(reset_stack=False)
        self.refresh_view()

    def _update_nav_buttons(self, current_channel_images):
        self.view.prev_sample_button.configure(state="normal" if self.well_index > 0 else "disabled")
        self.view.next_sample_button.configure(
            state="normal" if self.well_index < len(self.well_keys) - 1 else "disabled"
        )

        sites = self._site_numbers_for_current_well()
        try:
            site_index = sites.index(self.site_number)
        except ValueError:
            site_index = 0

        self.view.prev_site_button.configure(state="normal" if site_index > 0 else "disabled")
        self.view.next_site_button.configure(
            state="normal" if site_index < len(sites) - 1 else "disabled"
        )

        self.view.prev_stack_button.configure(state="normal" if self.stack_index > 0 else "disabled")
        self.view.next_stack_button.configure(
            state="normal" if self.stack_index < len(current_channel_images) - 1 else "disabled"
        )
