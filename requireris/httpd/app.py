from typing import Annotated

import jinja2
import fastapi
import fastapi.templating

from .fastapi_utils import AcceptHTML, FormOrJSON
from .schemas import InsertData, UpdateData
from ..totp import generate_totp


app = fastapi.FastAPI()
templates = fastapi.templating.Jinja2Templates(
    env=jinja2.Environment(
        loader=jinja2.PackageLoader('requireris.www'),
        autoescape=jinja2.select_autoescape(),
    ),
)


@app.get('/')
@app.get('/keys')
def index(
        request: fastapi.Request,
        accept_html: AcceptHTML,
        additional_fields: Annotated[list[str], fastapi.Query(alias='add-field')] = [],
):
    if accept_html:
        return templates.TemplateResponse(
            request,
            'index.html',
            {
                'keys': app.db.keys(),
                'additional_fields': additional_fields,
            }
        )
    return {
        'keys': {
            key: {
                '@get': {
                    'method': 'GET',
                    'href': f'{app.url}/keys/{key}',
                },
            }
            for key in app.db.keys()
        },
        '@list': {
            'method': 'GET',
            'href': f'{app.url}/keys',
        },
        '@insert': {
            '@method': 'POST',
            'href': f'{app.url}/keys',
            'template': {
                'key': 'string',
                'secret': 'string',
            },
        },
    }


@app.get('/keys/{key}')
@app.get('/get/{key}')
def get_key(
        key: str,
        request: fastapi.Request,
        accept_html: AcceptHTML,
        additional_fields: Annotated[list[str], fastapi.Query(alias='add-field')] = [],
        delete_fields: Annotated[list[str], fastapi.Query(alias='del-field')] = [],
):
    try:
        item = dict(app.db[key])
    except KeyError as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=f"Key {key!r} not found",
        )
    code = generate_totp(item.pop('secret'))
    if accept_html:
        common_fields = set(additional_fields) & set(delete_fields)
        for field in common_fields:
            additional_fields.remove(field)
            delete_fields.remove(field)
        return templates.TemplateResponse(
            request,
            'get.html',
            {
                'key': key,
                'code': code,
                'data': item,
                'additional_fields': additional_fields,
                'delete_fields': delete_fields,
            },
        )
    return {
        **item,
        'code': code,
        '@list': {
            'method': 'GET',
            'href': f'{app.url}/keys',
        },
        '@get': {
            'method': 'GET',
            'href': f'{app.url}/keys/{key}',
        },
        '@update': {
            'method': 'PUT',
            'href': f'{app.url}/keys/{key}',
            'template': {
                'secret': 'string',
            },
        },
        '@delete': {
            'method': 'DELETE',
            'href': f'{app.url}/keys/{key}',
        },
    }


@app.post('/new')
@app.post('/keys')
def insert_key(
        data: Annotated[InsertData, FormOrJSON()],
        request: fastapi.Request,
        accept_html: AcceptHTML,
):
    data = data.model_dump()
    key = data.pop('key')
    app.db[key] = data
    app.db.save()
    if accept_html:
        return fastapi.responses.RedirectResponse(
            f'/get/{key}',
            status_code=fastapi.status.HTTP_303_SEE_OTHER,
        )
    return get_key(key, request=request, accept_html=False)


@app.post('/del/{key}')
@app.delete('/keys/{key}')
def delete_key(key, request: fastapi.Request, accept_html: AcceptHTML):
    try:
        del app.db[key]
    except KeyError as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=f"Key {key!r} not found",
        )
    app.db.save()
    if accept_html:
        return fastapi.responses.RedirectResponse(
            '/',
            status_code=fastapi.status.HTTP_303_SEE_OTHER,
        )
    return fastapi.responses.Response(status_code=fastapi.status.HTTP_204_NO_CONTENT)


@app.post('/update/{key}')
@app.put('/keys/{key}')
@app.patch('/keys/{key}')
def update_key(
        key,
        data: Annotated[UpdateData, FormOrJSON()],
        request: fastapi.Request,
        accept_html: AcceptHTML,
):
    if not data.secret and key in app.db:
        data.secret = app.db[key]['secret']
    if request.method == 'PATCH':
        app.db[key] |= data.model_dump()
    else:
        app.db[key] = data.model_dump()
    app.db.save()
    if accept_html:
        return fastapi.responses.RedirectResponse(
            f'/get/{key}',
            status_code=fastapi.status.HTTP_303_SEE_OTHER,
        )
    return get_key(key, request=request, accept_html=False)
