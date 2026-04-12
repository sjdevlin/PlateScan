class ResultRunListPresenter:
    def __init__(self, view, db):
        self.view = view
        self.db = db
        self.view.res_bind_row_selection(self.on_res_row_selected)
        self.view.review_button.configure(command=self.review_result_run)
        self.selected_res_row = None
        self.refresh_view()

    def on_res_row_selected(self, _event):
        self.selected_res_row = self.view.get_id_of_selected_res_row()
        if self.selected_res_row is not None:
            self.view.enable_review_button()

    def refresh_view(self):
        results = self.db.get_all_result_runs()

        data = []
        for result in results:
            image_set = self.db.get_image_set_by_id(result.image_set_id)
            plate = self.db.get_plate_by_id(result.plate_id)

            data.append(
                (
                    result.id,
                    result.description,
                    result.start_date_time.strftime("%Y-%m-%d %H:%M") if result.start_date_time else "",
                    image_set.description if image_set else "",
                    plate.description if plate else "",
                )
            )

        self.view.list_results(data)
        self.view.disable_review_button()

    def review_result_run(self):
        from presenters import ResultRunDetailPresenter
        from views import ResultRunDetailView

        result_id = self.view.get_id_of_selected_res_row()
        if result_id is None:
            return

        result_detail_view = ResultRunDetailView()
        ResultRunDetailPresenter(view=result_detail_view, db=self.db, result_run_id=result_id)
