
from gsheet.src import GoogleSheetApiManagerEnableEvent, GoogleSheetApiManagerState, GoogleSheetApiManagerWrite


class GoogleSheetApiProvider:

    def __init__(self, google_sheet_manager, data_getter, run_in_thread=True):
        self.data_getter = data_getter
        self.google_sheet_manager = google_sheet_manager
        self.run_in_thread =run_in_thread

    def __enter__(self):
        def create_api(app):

            @app.get("/")
            async def get_gsheet_state():
                return self.google_sheet_manager.state

            @app.post("/")
            async def post_gsheet_state(data: GoogleSheetApiManagerState):
                self.google_sheet_manager.update_state(data)
                self.google_sheet_manager.update_all(self.data_getter(), run_in_thread=self.run_in_thread)
                return self.google_sheet_manager.state

            @app.post("/enabled")
            async def post_gsheet_enabled(data: GoogleSheetApiManagerEnableEvent):
                self.google_sheet_manager.state.enable = data.value
                self.google_sheet_manager.update_all(self.data_getter(), run_in_thread=self.run_in_thread)
                return GoogleSheetApiManagerEnableEvent(value=self.google_sheet_manager.state.enable)

            @app.post("/writes/add")
            async def add_gsheet_writes(data: list[GoogleSheetApiManagerWrite]):
                self.google_sheet_manager.state.writes.extend(data)
                self.google_sheet_manager.update_all(self.data_getter(), run_in_thread=self.run_in_thread)
                return self.google_sheet_manager.state.writes

            @app.post("/writes")
            async def post_gsheet_writes(data: list[GoogleSheetApiManagerWrite]):
                self.google_sheet_manager.state.writes = data
                self.google_sheet_manager.update_all(self.data_getter(), run_in_thread=self.run_in_thread)
                return self.google_sheet_manager.state.writes

            @app.get("/update_sheet")
            async def gsheet_update():

                if self.google_sheet_manager.state.enable:
                    try:
                        self.google_sheet_manager.update_all(self.data_getter(), run_in_thread=self.run_in_thread)
                        return {"success": True, "reason": None}
                    except Exception as err:
                        return {"success": False, "reason": {"exception": repr(err)}}
                else:
                    return {"success": False, "reason": {"state": {
                        "enable": False
                    }}}

        return create_api

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.google_sheet_manager.dump(exc_type, exc_val, exc_tb)
