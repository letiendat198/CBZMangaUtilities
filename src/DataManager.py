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


class ExportData:
    def __init__(self):
        self.file = FileHelper("export.json")
        if not self.file.exists():
            template = {
                "UC": "",
                "RC": "",
                "UBW": "",
                "RBW": "",
                "Include": [],  # Hash
                "Exclude": []   # Hash also
            }
            self._overwrite_dict(template)

    def _overwrite_dict(self, d):
        js = json.dumps(d)
        self.file.overwrite(js)

    def reset(self):
        template = {
            "UC": "",
            "RC": "",
            "UBW": "",
            "RBW": "",
            "Include": [],  # Hash
            "Exclude": []  # Hash also
        }
        self._overwrite_dict(template)

    def get_dict(self):
        return json.loads(self.file.read())

    def update_status(self, group, status):
        modified_dict = self.get_dict()
        modified_dict[group] = status
        self._overwrite_dict(modified_dict)

    def add_exclusion(self, file_hash):
        modified_dict = self.get_dict()
        include_set = set(modified_dict["Include"])
        exclude_set = set(modified_dict["Exclude"])
        if file_hash in include_set:
            include_set.remove(file_hash)
        exclude_set.add(file_hash)
        modified_dict["Include"] = sorted(include_set)
        modified_dict["Exclude"] = sorted(exclude_set)
        self._overwrite_dict(modified_dict)

    def add_inclusion(self, file_hash):
        modified_dict = self.get_dict()
        include_set = set(modified_dict["Include"])
        exclude_set = set(modified_dict["Exclude"])
        if file_hash in exclude_set:
            exclude_set.remove(file_hash)
        include_set.add(file_hash)
        modified_dict["Include"] = sorted(include_set)
        modified_dict["Exclude"] = sorted(exclude_set)
        self._overwrite_dict(modified_dict)

    def check_include(self, file_hash):
        exp_dict = self.get_dict()
        include_set = set(exp_dict["Include"])
        if file_hash in include_set:
            return True
        return False

    def check_exclude(self, file_hash):
        exp_dict = self.get_dict()
        exclude_set = set(exp_dict["Exclude"])
        if file_hash in exclude_set:
            return True
        return False


