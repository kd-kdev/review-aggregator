from pydantic import BaseModel
from datetime import date, datetime


class GameSchema(BaseModel):
    appid: int
    name: str
    capsule_imagev5: str | None
    developers: str | None
    publishers: str | None
    platforms: str | None
    release_date: date | None
    last_updated: datetime | None

    model_config = {"from_attributes": True}
