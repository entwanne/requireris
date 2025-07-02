from typing import Annotated

import fastapi
import pydantic


def _accept_html(accept: Annotated[str, fastapi.Header()] = '') -> bool:
    return 'text/html' in accept or 'application/xhtml+xml' in accept


AcceptHTML = Annotated[bool, fastapi.Depends(_accept_html)]


class FormOrJSON(fastapi.params.Depends):
    def __init__(self):
        super().__init__()
        self._data_type = None

    @property
    def dependency(self):
        return self._dependency

    @dependency.setter
    def dependency(self, value):
        if value is None:
            self._dependency = value
        else:
            self._data_type = value
            self._dependency = self._process

    async def _process(
            self,
            request: fastapi.Request,
            content_type: Annotated[str, fastapi.Header()] = '',
    ):
        if 'application/json' in content_type:
            data = await request.json()
        elif 'application/x-www-form-urlencoded' in content_type:
            data = await request.form()
        else:
            data = {}
        if self._data_type is not None:
            adapter = pydantic.TypeAdapter(self._data_type)
            try:
                data = adapter.validate_python(data)
            except pydantic.ValidationError as e:
                raise fastapi.exceptions.RequestValidationError(e.errors())
        return data
