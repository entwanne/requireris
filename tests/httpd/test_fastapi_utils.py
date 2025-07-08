from typing import Annotated

import fastapi
import pydantic
import pytest
from fastapi.testclient import TestClient

from requireris.httpd.fastapi_utils import AcceptHTML, FormOrJSON


def test_accept_html():
    app = fastapi.FastAPI()

    @app.get('/')
    def _route(accept_html: AcceptHTML):
        return {'accept_html': accept_html}

    cli = TestClient(app)

    assert cli.get('/').json() == {'accept_html': False}
    assert cli.get('/', headers={'Accept': ''}).json() == {'accept_html': False}
    assert cli.get('/', headers={'Accept': 'text/plain,application/json'}).json() == {'accept_html': False}
    assert cli.get('/', headers={'Accept': 'text/html'}).json() == {'accept_html': True}
    assert cli.get('/', headers={'Accept': 'application/json,text/html'}).json() == {'accept_html': True}
    assert cli.get('/', headers={'Accept': 'application/xhtml+xml'}).json() == {'accept_html': True}
    assert cli.get('/', headers={'Accept': 'text/xhtml+xml'}).json() == {'accept_html': False}
    assert cli.get('/', headers={'Accept': 'application/html'}).json() == {'accept_html': False}


def test_form_or_json():
    class DataModel(pydantic.BaseModel):
        name: str
        value: int

    class DataModelExtra(pydantic.BaseModel):
        name: str
        value: int
        model_config = pydantic.ConfigDict(extra='allow')

    app = fastapi.FastAPI()

    @app.post('/dict')
    def _dict_route(data: Annotated[dict, FormOrJSON()]):
        return {'type': type(data).__name__, 'data': data}

    @app.post('/model')
    def _model_route(data: Annotated[DataModel, FormOrJSON()]):
        return {'type': type(data).__name__, 'data': data}

    @app.post('/model-extra')
    def _model_extra_route(data: Annotated[DataModelExtra, FormOrJSON()]):
        return {'type': type(data).__name__, 'data': data}

    cli = TestClient(app)

    assert cli.post('/dict').json() == {'type': 'dict', 'data': {}}
    assert cli.post('/dict', json={}).json() == {'type': 'dict', 'data': {}}
    assert cli.post('/dict', json={'abc': 'def'}).json() == {'type': 'dict', 'data': {'abc': 'def'}}
    assert cli.post('/dict', data={}).json() == {'type': 'dict', 'data': {}}
    assert cli.post('/dict', data={'abc': 'def'}).json() == {'type': 'dict', 'data': {'abc': 'def'}}

    resp = cli.post('/model')
    assert resp.status_code == 422
    assert [(e['type'], e['loc']) for e in resp.json()['detail']] == [('missing', ['name']), ('missing', ['value'])]

    resp = cli.post('/model', json={})
    assert resp.status_code == 422
    assert [(e['type'], e['loc']) for e in resp.json()['detail']] == [('missing', ['name']), ('missing', ['value'])]

    resp = cli.post('/model', data={})
    assert resp.status_code == 422
    assert [(e['type'], e['loc']) for e in resp.json()['detail']] == [('missing', ['name']), ('missing', ['value'])]

    assert cli.post('/model', json={'name': 'test', 'value': 1}).json() == {'type': 'DataModel', 'data': {'name': 'test', 'value': 1}}
    assert cli.post('/model', json={'name': 'test', 'value': 1, 'extra': 'extra'}).json() == {'type': 'DataModel', 'data': {'name': 'test', 'value': 1}}
    assert cli.post('/model', data={'name': 'test', 'value': 1}).json() == {'type': 'DataModel', 'data': {'name': 'test', 'value': 1}}
    assert cli.post('/model', data={'name': 'test', 'value': 1, 'extra': 'extra'}).json() == {'type': 'DataModel', 'data': {'name': 'test', 'value': 1}}

    assert cli.post('/model-extra', json={'name': 'test', 'value': 1}).json() == {'type': 'DataModelExtra', 'data': {'name': 'test', 'value': 1}}
    assert cli.post('/model-extra', json={'name': 'test', 'value': 1, 'extra': 'extra'}).json() == {'type': 'DataModelExtra', 'data': {'name': 'test', 'value': 1, 'extra': 'extra'}}
    assert cli.post('/model-extra', data={'name': 'test', 'value': 1}).json() == {'type': 'DataModelExtra', 'data': {'name': 'test', 'value': 1}}
    assert cli.post('/model-extra', data={'name': 'test', 'value': 1, 'extra': 'extra'}).json() == {'type': 'DataModelExtra', 'data': {'name': 'test', 'value': 1, 'extra': 'extra'}}
