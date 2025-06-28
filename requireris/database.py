from configparser import ConfigParser, UNNAMED_SECTION
from base64 import b32decode
from logging import getLogger

from .exceptions import MissingSecret, WrongSecret

logger = getLogger(__name__)


class Database:
    def __init__(self, path=None, **kwargs):
        self.path = path

        missing_secrets = [k for k, item in kwargs.items() if 'secret' not in item]
        if missing_secrets:
            raise MissingSecret(missing_secrets)

        self._data = kwargs

    def load(self, missing_ok=False):
        self._data.clear()

        config = ConfigParser()

        try:
            with self.path.open() as file:
                config.read_file(file)
        except FileNotFoundError:
            if missing_ok:
                return
            else:
                raise

        for key, section in config.items():
            if 'secret' in section:
                self._data[key] = dict(section)
            elif key != 'DEFAULT':
                logger.warning("No secret in section %s, skipping", key)

    def save(self):
        config = ConfigParser(allow_unnamed_section=True)

        for key, item in self.items():
            config.add_section(key)
            for name, value in item.items():
                config.set(key, name, value)

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

    def __setitem__(self, key, item):
        if 'secret' not in item:
            raise MissingSecret(key)
        try:
            b32decode(item['secret'].upper())
        except:
            raise WrongSecret(key)
        self._data[key] = item

    def __delitem__(self, key):
        del self._data[key]
