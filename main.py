# This is a sample Python script.
import json
from dataclasses import asdict

import requests
import uvicorn
from fastapi import FastAPI

from gsheet import GoogleSheetApiManager, GoogleSheetApiManagerState
from gsheet.api import GoogleSheetApiProvider


def data_getter():
    url="http://0.0.0.0:7711/cxm/api/v2/mfb_sw_l2/stats"
    return requests.get(url).json()

with open("test/test_spec.json") as f:
    spec=json.load(f)

class TestGoogleSheetApiManager(GoogleSheetApiManager):
    def dump(self, exc_type=None, exc_val=None, exc_tb=None):
        super().dump(exc_type, exc_val, exc_tb)
        with open("test/test_spec.json","w") as fl:
            json.dump( asdict(self.state),fl, indent=2)




if __name__ == "__main__":
    manager = TestGoogleSheetApiManager(GoogleSheetApiManagerState.from_dict(spec))
    app = FastAPI()

    with GoogleSheetApiProvider(manager, data_getter, run_in_thread=False) as api:
        api(app)
        uvicorn.run(app, host="0.0.0.0",port=7088)