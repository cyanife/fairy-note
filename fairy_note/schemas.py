from typing import List, Optional, Union

from pydantic import BaseModel, Schema
from starlette.datastructures import Secret


class Database(BaseModel):
    host: str = Schema("localhost", description="Server host.")
    port: Optional[Union[str, int]] = Schema(None, description="Server access port.")
    username: Optional[str] = Schema(None, alias="user", description="Username")
    password: Optional[Union[str, Secret]] = Schema(None, description="Password")
    database: str = Schema(..., description="Database name.")

    class Config:
        arbitrary_types_allowed = True
        allow_population_by_alias = True


class Axis(BaseModel):
    data: Optional[List[str]]


class Series(BaseModel):
    name: str


class ChartSeries(Series):
    data: Optional[List[str]]


class Chart(BaseModel):
    xAxis: Axis
    series: List[ChartSeries]


class UserRanking(BaseModel):
    name: str
    value: int


class RankingSeries(Series):
    data: Optional[List[UserRanking]]


class Ranking(BaseModel):
    series: List[RankingSeries]


class DashBoard(BaseModel):
    trendData: Chart
    stackedData: Chart
    rankingData: Ranking
