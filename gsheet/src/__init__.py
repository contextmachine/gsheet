import abc
import dataclasses
import functools
import os
import typing
import dotenv

dotenv.load_dotenv(".env")
from gsheet.stats import cross_aggregate, resort
from gsheet.utils import get_service_sacc
import json

_table_keys = ('name',
               'tag',
               'arch_type',
               'eng_type',
               'block',
               'zone',
               'cut',
               'pair_name',
               'pair_index',
               'mount',
               'mount_date',
               'area')


@dataclasses.dataclass
class GoogleSheetApiObject:

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, dct) -> typing.Self: ...


@dataclasses.dataclass
class GoogleSheetApiManagerWrite:
    sheet_range: str
    key: typing.Union[str, list[str]]
    mask: str = "cut"
    sep: str = " "
    method: str = "default"

    @classmethod
    def from_dict(cls, dct):
        return cls(**dct)


@dataclasses.dataclass
class GoogleSheetApiManagerState:
    sheet_id: str
    main_sheet_range: str
    table_keys: list[str]
    writes: list[GoogleSheetApiManagerWrite]
    enable: bool = True
    credentials: str = "GOOGLE_KF"

    @classmethod
    def from_dict(cls, dct):
        writes = dct.get("writes", None)
        if writes is None:

            dct['writes'] = []
        else:
            dct['writes'] = [GoogleSheetApiManagerWrite.from_dict(write) for write in writes]
        return cls(**dct)


@dataclasses.dataclass
class GoogleSheetApiManagerEnableEvent:
    value: bool


class GoogleSheetApiManager:
    def __init__(self, state: GoogleSheetApiManagerState = None, /,
                 sheet_id=None,

                 main_sheet_range="SW_L2_test!A1",

                 table_keys=_table_keys, writes=None, enable=True, credentials="GOOGLE_KF"):
        if state:
            self.state = state
        else:
            if writes is None:
                writes = []
            self.state = GoogleSheetApiManagerState(
                sheet_id=sheet_id,
                credentials=credentials,
                main_sheet_range=main_sheet_range,
                table_keys=table_keys,
                writes=writes,
                enable=enable

            )
        self.service = get_service_sacc(self.get_keyfile_dict())
        self.sheet = self.service.spreadsheets()
        self.dispatch_table = dict(default=self.dict_bind(cross_aggregate))

    def get_keyfile_dict(self):
        return json.loads(os.getenv(self.state.credentials))

    def update_state(self, state: GoogleSheetApiManagerState):
        self.state = state

    def resort_table(self, data):
        return resort(data, self.state.table_keys)

    def update_sheet(self, data, sheet_range):
        if self.state.enable:
            return self.sheet.values().update(
                spreadsheetId=self.state.sheet_id,
                range=sheet_range,
                valueInputOption='RAW',
                body={'values': data}).execute()

    def update_all(self, data, run_in_thread=True):
        import threading as th
        if self.state.enable:
            data_ = data

            def proc():
                self.update_sheet(list(self.resort_table(data_)),
                                  sheet_range=self.state.main_sheet_range)
                for write in self.state.writes:
                    res=self.get_method(name=write.method)(data_,
                                                       key=write.key,
                                                       mask=write.mask,
                                                       sep=write.sep)
                    print(res)
                    self.update_sheet(res,
                                      sheet_range=write.sheet_range)

                print("google sheet updated!")
            if run_in_thread:
                thread = th.Thread(target=proc)
                thread.start()
            else:
                proc()
        else:
            print("google sheet update disabled")

    def __call__(self, name=None):
        self._fn_name = name

        def wrapper(fn):
            if self._fn_name is None:
                self._fn_name = fn.__name__

            self.dispatch_table[str(self._fn_name)] = self.dict_bind(fn)

            return fn

        return wrapper
    def dict_bind(self, fn):
        def wrapper(*args, **kwargs):
            res=fn(*args,**kwargs)
            return list(res.items())
        return wrapper

    def get_method(self, name: str):
        return self.dispatch_table[name]

    def dump(self, exc_type=None, exc_val=None, exc_tb=None):
        print(exc_type, exc_val, exc_tb)
        print("dump")
