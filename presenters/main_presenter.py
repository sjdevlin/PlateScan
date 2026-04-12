
class MainPresenter:
    def __init__(self, view, db):
        self.view = view
        self.db = db

        self.view.manage_image_sets_button.configure(command=self.open_manage_image_sets_window)
        self.view.launch_imaging_run_button.configure(command=self.open_launch_imaging_run_window)
        self.view.review_results_button.configure(command=self.open_review_results_window)
        self.view.image_sandbox_button.configure(command=self.open_image_sandbox_window)

    def open_manage_image_sets_window(self):
        from presenters import ImageSetManagerPresenter
        from views import ImageSetManagerView

        view = ImageSetManagerView()
        ImageSetManagerPresenter(view, self.db)

    def open_launch_imaging_run_window(self):
        from presenters import ImagingRunLauncherPresenter
        from views import ImagingRunLauncherView

        view = ImagingRunLauncherView()
        ImagingRunLauncherPresenter(view, self.db)

    def open_review_results_window(self):
        from presenters import ResultRunListPresenter
        from views import ResultRunListView

        view = ResultRunListView()
        ResultRunListPresenter(view, self.db)

    def open_image_sandbox_window(self):
        from presenters import ImageSandboxPresenter
        from views import ImageSandboxView

        view = ImageSandboxView()
        ImageSandboxPresenter(view, self.db)
