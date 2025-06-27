from configparser import ConfigParser, UNNAMED_SECTION
from base64 import b32decode

from .exceptions import WrongSecret


class Database:
    def __init__(self, path=None, **data):
        self.path = path
        self._data = data

    def load(self, missing_ok=False):
        self._data.clear()

        config = ConfigParser(allow_unnamed_section=True)

        try:
            with self.path.open() as file:
                config.read_file(file)
        except FileNotFoundError:
            if missing_ok:
                return
            else:
                raise

        if not config.has_section(UNNAMED_SECTION):
            return

        secrets = config[UNNAMED_SECTION]
        return self._data.update({
            key: secret.replace(' ', '').upper()
            for key, secret in secrets.items()
        })

    def save(self):
        config = ConfigParser(allow_unnamed_section=True)
        config.read_string('a=b')
        config.remove_option(UNNAMED_SECTION, 'a')

        for key, secret in self.items():
            config.set(UNNAMED_SECTION, key, secret)

        with self.path.open('w') as file:
            config.write(file)

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, secret):
        try:
            b32decode(secret.replace(' ', '').upper())
        except:
            raise WrongSecret
        self._data[key] = secret

    def __delitem__(self, key):
        del self._data[key]
