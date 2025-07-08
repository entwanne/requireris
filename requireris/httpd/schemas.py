import pydantic


class InsertData(pydantic.BaseModel):
    key: str
    secret: str

    model_config = pydantic.ConfigDict(extra='allow')


class UpdateData(pydantic.BaseModel):
    secret: str | None = None

    model_config = pydantic.ConfigDict(extra='allow')
