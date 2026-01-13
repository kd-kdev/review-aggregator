from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


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


class GameDetailResponseSchema(BaseModel):
    appid: int
    name: str
    capsule_image_v5: str | None
    release_date: Optional[datetime]
    review_score_desc: Optional[str]
    total_reviews: int
    total_positive: int
    total_negative: int
