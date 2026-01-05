from typing import List, Optional
from pydantic import BaseModel


class PerDayItem(BaseModel):
    date: str  # ISO date YYYY-MM-DD
    day: str   # short day label, e.g. Mon
    total_sales: float
    total_earnings: float
    orders_count: int


class Datasets(BaseModel):
    sales: List[float]
    earnings: List[float]
    orders: List[int]


class Totals(BaseModel):
    week_total_sales: float
    week_total_earnings: float
    week_orders_count: int


class WeeklySummaryResponse(BaseModel):
    week_start: str
    week_end: str
    labels: List[str]
    per_day: List[PerDayItem]
    datasets: Datasets
    totals: Optional[Totals]
