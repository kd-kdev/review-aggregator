from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ReviewSchema(BaseModel):
    recommendationid: int
    appid: int

    review: str
    voted_up: bool

    steam_purchase: Optional[bool] = None
    received_for_free: Optional[bool] = None
    written_during_early_access: Optional[bool] = None
    primarily_steam_deck: Optional[bool] = None

    timestamp_created: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReviewKeywordSummarySchema(BaseModel):
    keyword: str
    occurrences: int
    reviews_with_keyword: int


class ReviewKeywordResponseSchema(BaseModel):
    keyword: str
    summary: ReviewKeywordSummarySchema
    reviews: List[ReviewSchema]
