from pydantic import BaseModel


class QueryMeta(BaseModel):
    num_reviews: int
    review_score: int
    total_positive: int
    total_negative: int
    total_reviews: int
