import json
import os

from FileHelper import *


class DataManager:
    def __init__(self):
        self.f = [FileHelper("data.json"), FileHelper("hash.json"), FileHelper("group.json")]

        for idx, file in enumerate(self.f):
            if not file.exists():
                d = {}
                self.overwrite_dict(d, idx)

    def get_dict(self, idx):
        return json.loads(self.f[idx].read())

    def overwrite_dict(self, d, idx):
        js = json.dumps(d)
        self.f[idx].overwrite(js)


