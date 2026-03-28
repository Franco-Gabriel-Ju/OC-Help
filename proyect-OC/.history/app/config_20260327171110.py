import json
import os


class PreferencesManager:
    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser("~"), ".oc_help")
        self.config_file = os.path.join(self.config_dir, "preferences.json")
        self.defaults = {
            "editor": {
                "font_family": "Courier",
                "font_size": 10,
            },
            "theme": {
                "mode": "light",
            },
        }
        self.preferences = self.load()

    def load(self):
        if not os.path.isfile(self.config_file):
            return self._deep_copy_defaults()

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            return self._merge_with_defaults(loaded)
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            return self._deep_copy_defaults()

    def save(self):
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.preferences, f, indent=2, ensure_ascii=True)

    def get(self, section, key):
        return self.preferences.get(section, {}).get(key, self.defaults.get(section, {}).get(key))

    def set(self, section, key, value):
        if section not in self.preferences:
            self.preferences[section] = {}

        value = self._sanitize(section, key, value)
        self.preferences[section][key] = value

    def _sanitize(self, section, key, value):
        if section == "editor" and key == "font_size":
            try:
                size = int(value)
            except (TypeError, ValueError):
                return self.defaults["editor"]["font_size"]
            return max(8, min(24, size))

        if section == "editor" and key == "font_family":
            allowed = ["Courier", "Consolas", "Lucida Console", "Courier New"]
            return value if value in allowed else self.defaults["editor"]["font_family"]

        if section == "theme" and key == "mode":
            return value if value in ("light", "dark") else self.defaults["theme"]["mode"]

        return value

    def _merge_with_defaults(self, loaded):
        merged = self._deep_copy_defaults()
        if not isinstance(loaded, dict):
            return merged

        for section, values in loaded.items():
            if section not in merged or not isinstance(values, dict):
                continue
            for key, value in values.items():
                if key in merged[section]:
                    merged[section][key] = self._sanitize(section, key, value)
        return merged

    def _deep_copy_defaults(self):
        return {
            section: dict(values)
            for section, values in self.defaults.items()
        }
