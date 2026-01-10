from pydantic import BaseModel
from typing import List


class GameOverviewSchema(BaseModel):
    appid: int
    name: str
    capsule_image: str | None
    total_reviews: int
    positive_pct: float
    negative_pct: float


class GameOverviewResponse(BaseModel):
    data: List[GameOverviewSchema]
    count: int
