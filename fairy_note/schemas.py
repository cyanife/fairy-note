from typing import List, Optional, Union

from pydantic import UUID4, BaseModel, Schema, validator
from starlette.datastructures import Secret
from tortoise.contrib.pydantic import pydantic_model_creator

from .models import DouyuBarrage, UserModel

# Config


class Database(BaseModel):
    host: str = Schema("localhost", description="Server host.")
    port: Optional[Union[str, int]] = Schema(None, description="Server access port.")
    username: Optional[str] = Schema(None, alias="user", description="Username")
    password: Optional[Union[str, Secret]] = Schema(None, description="Password")
    database: str = Schema(..., description="Database name.")

    class Config:
        arbitrary_types_allowed = True
        allow_population_by_alias = True


# Barrages


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


DouyuBarrage_Schema = pydantic_model_creator(DouyuBarrage, name="DouyuBarrage")


class Message(BaseModel):
    type: str
    text: str


class BarrageList(BaseModel):
    barrages: List[DouyuBarrage_Schema]
    messages: Optional[List[Message]]


# USER


User = pydantic_model_creator(UserModel, name="User", exclude=("hashed_password",))


class UserCreate(
    pydantic_model_creator(
        UserModel,
        exclude=(
            "id",
            "hashed_password",
        ),
    )
):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str]
    password: Optional[str]
    is_active: Optional[bool]


class DeleteResult(BaseModel):
    message: str


class ChangePasswordForm:
    oldPassword: str
    password: str


# AUTH


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    username: Optional[str] = None
