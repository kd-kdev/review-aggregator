from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, Any


class GameSchema(BaseModel):
    appid: int
    name: str
    capsule_imagev5: Optional[str] = None
    developers: Optional[str] = None
    publishers: Optional[str] = None
    platforms: Optional[str] = None
    release_date: Optional[date] = None
    last_updated: Optional[datetime] = None

    model_config = {"from_attributes": True}


class QuerySummarySchema(BaseModel):
    appid: int
    num_reviews: Optional[int] = None
    review_score: Optional[int] = None
    review_score_desc: Optional[str] = None
    total_positive: Optional[int] = None
    total_negative: Optional[int] = None
    total_reviews: Optional[int] = None
    cursor: Optional[str] = None
    updated_at: Optional[datetime] = None
    raw_json: Optional[Any] = None

    model_config = {"from_attributes": True}


class ReviewSchema(BaseModel):
    recommendationid: int
    appid: int
    steamid: int
    language: Optional[str] = None
    review: Optional[str] = None
    voted_up: Optional[bool] = None
    votes_up: Optional[int] = None
    votes_funny: Optional[int] = None
    timestamp_created: Optional[datetime] = None
    timestamp_updated: Optional[datetime] = None
    steam_purchase: Optional[bool] = None
    received_for_free: Optional[bool] = None
    written_during_early_access: Optional[bool] = None
    primarily_steam_deck: Optional[bool] = None
    raw_json: Optional[Any] = None

    model_config = {"from_attributes": True}
