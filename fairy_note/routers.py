from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import UUID4
from tortoise.contrib.fastapi import HTTPNotFoundError
from tortoise.query_utils import Q
from tortoise.transactions import in_transaction

from .auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
)
from .models import DouyuBarrage, UserModel
from .schemas import (
    Axis,
    BarrageList,
    Chart,
    ChartSeries,
    DashBoard,
    DeleteResult,
    DouyuBarrage_Schema,
    Message,
    Ranking,
    RankingSeries,
    Token,
    TokenPayload,
    User,
    UserCreate,
    UserRanking,
    UserUpdate,
)
from .settings import (
    API_PREFIX,
    BARRAGE_TABLE_NAME,
    JWT_EXPIRE_HOURS,
    JWT_SECRET_KEY,
    ROOM_ID,
)

# BARRAGES


class SortMode(str, Enum):
    ASC = "ASC"
    DESC = "DESC"


def get_barrage_router():
    router = APIRouter()

    @router.get(
        "/barrages",
        response_model=BarrageList,
        dependencies=[Depends(get_current_active_user)],
    )
    async def get_barrage(
        request: Request,
        sort: SortMode,
        username: Optional[str] = None,
        dt_min: Optional[datetime] = None,
        dt_max: Optional[datetime] = None,
    ):
        query = Q()
        order_by = None
        if username:
            query = query & Q(nickname__icontains=username)
        if dt_min:
            query = query & Q(time__gte=dt_min)
        if dt_max:
            query = query & Q(time__lte=dt_max)
        if sort == SortMode.ASC:
            order_by = "time"
        else:
            order_by = "-time"
        barrages = await DouyuBarrage_Schema.from_queryset(
            DouyuBarrage.filter(query).order_by(order_by).limit(1000)
        )
        barrage_list = BarrageList(barrages=barrages)
        if len(barrages) == 1000:
            barrage_list.messages = [
                Message(type="warn", text="符合条件的记录过多，显示最近的1000条弹幕。")
            ]
        return barrage_list

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
        dependencies=[Depends(get_current_active_user)],
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

    # USER


def get_user_routes() -> APIRouter:
    router = APIRouter()

    @router.get(
        "/users",
        response_model=List[User],
        dependencies=[Depends(get_current_active_user)],
    )
    async def get_users():
        return await User.from_queryset(UserModel.all())

    @router.post(
        "/users",
        response_model=User,
        dependencies=[Depends(get_current_active_user)],
    )
    async def create_user(user: UserCreate):
        user_dict = user.dict(exclude_unset=True)
        user_dict["hashed_password"] = get_password_hash(user_dict["password"])
        user_obj = await UserModel.create(**user_dict)
        return await User.from_tortoise_orm(user_obj)

    @router.get(
        "/users/me",
        response_model=User,
        dependencies=[Depends(get_current_active_user)],
    )
    def get_current_user(current_user: User = Depends(get_current_active_user)):
        return current_user

    @router.get(
        "/users/{user_id}",
        response_model=User,
        responses={404: {"model": HTTPNotFoundError}},
        dependencies=[Depends(get_current_active_user)],
    )
    async def get_user(user_id: int):
        return await User.from_queryset_single(UserModel.get(id=user_id))

    @router.put(
        "/users/{user_id}",
        response_model=User,
        responses={404: {"model": HTTPNotFoundError}},
        dependencies=[Depends(get_current_active_user)],
    )
    async def update_user(user_id: int, user: UserUpdate):
        user_obj = await UserModel.get(id=user_id)
        update_dict = user.dict(exclude_unset=True)
        if update_dict["password"]:
            user_obj.hashed_password = get_password_hash(update_dict.pop("password"))
        await user_obj.update_from_dict(update_dict).save()
        return await User.from_tortoise_orm(user_obj)

    @router.delete(
        "/users/{user_id}",
        response_model=DeleteResult,
        responses={404: {"model": HTTPNotFoundError}},
        dependencies=[Depends(get_current_active_user)],
    )
    async def delete_user(user_id: int):
        deleted_count = await UserModel.filter(id=user_id).delete()
        if not deleted_count:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        return DeleteResult(message=f"Deleted user {user_id}")

    return router


# AUTH


def get_auth_router() -> APIRouter:
    router = APIRouter()

    @router.post("/token", response_model=Token)
    async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
        user = await authenticate_user(form_data.username, form_data.password)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(hours=JWT_EXPIRE_HOURS)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    return router


def init_app(app, **kwargs):

    app.include_router(get_barrage_router(), prefix=API_PREFIX, tags=["barrages"])
    app.include_router(get_dashboard_routers(), prefix=API_PREFIX, tags=["dashboard"])
    app.include_router(get_user_routes(), prefix=API_PREFIX, tags=["users"])
    app.include_router(get_auth_router(), prefix=API_PREFIX, tags=["auth"])

    # app.include_router(router)
