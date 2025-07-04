import pydantic
import pytest

from requireris.httpd.schemas import InsertData, UpdateData


def test_insert_data():
    schema = InsertData(key='site1', secret='AAAAAAAA')
    assert schema.model_dump() == {'key': 'site1', 'secret': 'AAAAAAAA'}


def test_insert_data_missing_values():
    with pytest.raises(pydantic.ValidationError) as e:
        InsertData()

    errors = [
        (err['type'], err['loc'])
        for err in e.value.errors()
    ]
    assert errors == [('missing', ('key',)), ('missing', ('secret',))]


def test_insert_data_extra_values():
    schema = InsertData(key='site1', secret='AAAAAAAA', foo='bar', baz='spam')
    assert schema.model_dump() == {'key': 'site1', 'secret': 'AAAAAAAA', 'foo': 'bar', 'baz': 'spam'}


def test_update_data():
    schema = UpdateData(secret='AAAAAAAA')
    assert schema.model_dump() == {'secret': 'AAAAAAAA'}


def test_update_data_no_values():
    schema = UpdateData()
    assert schema.model_dump() == {'secret': None}


def test_update_data_extra_values():
    schema = UpdateData(secret='AAAAAAAA', foo='bar', baz='spam')
    assert schema.model_dump() == {'secret': 'AAAAAAAA', 'foo': 'bar', 'baz': 'spam'}
