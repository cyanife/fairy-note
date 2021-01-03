from datetime import datetime
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, Depends, Request
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication
from fastapi_users.db import TortoiseUserDatabase
from tortoise.query_utils import Q
from tortoise.transactions import in_transaction

from .models import (
    DouyuBarrage,
    DouyuBarrage_Pydantic,
    User,
    UserCreate,
    UserDB,
    UserModel,
    UserUpdate,
)
from .schemas import (
    Axis,
    Chart,
    ChartSeries,
    DashBoard,
    Ranking,
    RankingSeries,
    UserRanking,
)
from .settings import BARRAGE_TABLE_NAME, JWT_EXPIRE_SECONDS, JWT_SECRET_KEY, ROOM_ID

jwt_authentication = JWTAuthentication(
    secret=JWT_SECRET_KEY,
    lifetime_seconds=JWT_EXPIRE_SECONDS,
    tokenUrl="/auth/jwt/login",
)

user_db = TortoiseUserDatabase(UserDB, UserModel)

fastapi_users = FastAPIUsers(
    user_db,
    [jwt_authentication],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)


class SortMode(str, Enum):
    ASC = "ASC"
    DESC = "DESC"


def get_barrage_router():
    router = APIRouter()

    @router.get(
        "/barrages",
        response_model=List[DouyuBarrage_Pydantic],
        dependencies=[Depends(fastapi_users.get_current_active_user)],
    )
    async def get_barrage(
        request: Request,
        sort: SortMode,
        username: Optional[str] = None,
        dt_min: Optional[datetime] = None,
        dt_max: Optional[datetime] = None,
    ):
        query = Q()
        if username:
            query = query & Q(nickname__icontains=username)
        if dt_min:
            query = query & Q(time__gte=dt_min)
        if dt_max:
            query = query & Q(time__lte=dt_max)
        if sort == SortMode.ASC:
            return await DouyuBarrage_Pydantic.from_queryset(
                DouyuBarrage.filter(query).order_by("time")
            )
        else:
            return await DouyuBarrage_Pydantic.from_queryset(
                DouyuBarrage.filter(query).order_by("-time")
            )

    return router


async def get_trend_data() -> Optional[dict]:
    async with in_transaction() as conn:
        res = await conn.execute_query(
            f"""
                SELECT DATE_TRUNC('day', time),
                    COUNT(*)
                FROM {BARRAGE_TABLE_NAME}
                WHERE time > NOW() - INTERVAL '1 week'
                GROUP BY DATE_TRUNC('day', time)
                ORDER BY MIN(time)
            """
        )
        rows = res[1]

        axis_data = [row[0].strftime("%Y/%m/%d") for row in rows]
        xAxis = Axis(data=axis_data)

        series_data = [row[1] for row in rows]
        series = ChartSeries(name="弹幕数量", data=series_data)

        trend_data = Chart(xAxis=xAxis, series=[series])

    return trend_data


async def get_stacked_data() -> Optional[dict]:
    async with in_transaction() as conn:
        res = await conn.execute_query(
            f"""
            SELECT DATE_TRUNC('day', time) AS stat_date,
                   COUNT(*) AS all_count,
                   COUNT(*) FILTER
                       (WHERE chatmsg->>'brid' = '{ROOM_ID}') AS fans_count,
                   COUNT(*) FILTER
                       (WHERE chatmsg->'nc' IS NOT NULL) AS noble_count
              FROM {BARRAGE_TABLE_NAME}
             WHERE time > now() - INTERVAL '1 week'
             GROUP BY DATE_TRUNC('day', time)
             ORDER BY MIN(time)
            """
        )
        rows = res[1]

        axis_data = [row[0].strftime("%Y/%m/%d") for row in rows]
        xAxis = Axis(data=axis_data)

        normal_series_data = [row[1] - row[2] - row[3] for row in rows]
        normal_series = ChartSeries(name="普通弹幕", data=normal_series_data)
        fans_series_data = [row[2] for row in rows]
        fans_series = ChartSeries(name="粉丝团弹幕", data=fans_series_data)
        noble_series_data = [row[3] for row in rows]
        noble_series = ChartSeries(name="贵族弹幕", data=noble_series_data)

        stacked_data = Chart(
            xAxis=xAxis, series=[normal_series, fans_series, noble_series]
        )

    return stacked_data


async def get_ranking_data() -> Optional[dict]:
    async with in_transaction() as conn:
        res = await conn.execute_query(
            f"""
            WITH name AS (
                SELECT DISTINCT ON (userid)
                       userid, nickname
                  FROM {BARRAGE_TABLE_NAME}
                 WHERE time > NOW() - INTERVAL '24 hours'
              ORDER BY userid, time DESC
              )

            SELECT rank.*, name.nickname
              FROM
              (
                SELECT userid,
                       count(*)
                  FROM {BARRAGE_TABLE_NAME}
                 WHERE time > NOW() - INTERVAL '24 hours'
              GROUP BY userid
              ) rank
            INNER JOIN name
                ON name.userid = rank.userid
            ORDER BY count DESC
            LIMIT 10
            """
        )
        rows = res[1]
        series_data = [UserRanking(name=row[2], value=row[1]) for row in rows]
        ranking_series = RankingSeries(name="发送弹幕数", data=series_data)

        ranking_data = Ranking(series=[ranking_series])

    return ranking_data


def get_dashboard_routers() -> APIRouter:
    router = APIRouter()

    @router.get(
        "/dashboard",
        response_model=DashBoard,
        dependencies=[Depends(fastapi_users.get_current_active_user)],
    )
    async def get_dashboard_data(request: Request):
        trend_data = await get_trend_data()
        stacked_data = await get_stacked_data()
        ranking_data = await get_ranking_data()

        dashboard_data = DashBoard(
            trendData=trend_data,
            stackedData=stacked_data,
            rankingData=ranking_data,
        )

        return dashboard_data

    return router


def init_app(app, **kwargs):
    app.include_router(
        fastapi_users.get_auth_router(jwt_authentication),
        prefix="/auth/jwt",
        tags=["auth"],
    )
    # app.include_router(
    #     fastapi_users.get_register_router(),
    #     prefix="/auth",
    #     tags=["auth"],
    # )
    app.include_router(
        fastapi_users.get_reset_password_router(JWT_SECRET_KEY),
        prefix="/auth",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_users_router(), prefix="/users", tags=["users"]
    )
    app.include_router(get_barrage_router(), tags=["barrages"])
    app.include_router(get_dashboard_routers(), tags=["dashboard"])

    # app.include_router(router)
