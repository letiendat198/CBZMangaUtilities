import json
from FileHelper import FileHelper


class SettingsManager:
    def __init__(self):
        self.templates = {
            "thread_count": 6,
            "skip_downloaded": True,
            "skip_have_url": True
        }
        self.settings_file = FileHelper("settings.json")
        if not self.settings_file.exists():
            self.settings_file.overwrite(json.dumps(self.templates))
        self.settings = json.loads(self.settings_file.read())
        self.templates.update(self.settings)
        self.settings = self.templates

    def update(self):
        js = json.dumps(self.settings)
        self.settings_file.overwrite(js)

    def reload(self):
        if not self.settings_file.exists():
            self.settings_file.overwrite(json.dumps(self.templates))
        self.settings = json.loads(self.settings_file.read())
        self.templates.update(self.settings)
        self.settings = self.templates
        return self.settings
