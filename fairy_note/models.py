from fastapi_users import models as user_models
from fastapi_users.db import TortoiseBaseUserModel
from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator

from .settings import BARRAGE_TABLE_NAME


class User(user_models.BaseUser):
    pass


class UserCreate(user_models.BaseUserCreate):
    pass


class UserUpdate(User, user_models.BaseUserUpdate):
    pass


class UserDB(User, user_models.BaseUserDB):
    pass


class UserModel(TortoiseBaseUserModel):
    pass


class DouyuBarrage(models.Model):

    id = fields.IntField(pk=True)
    userid = fields.CharField(max_length=20)
    nickname = fields.CharField(max_length=100)
    time = fields.DatetimeField()

    chatmsg = fields.JSONField()

    class Meta:
        table = BARRAGE_TABLE_NAME


DouyuBarrage_Pydantic = pydantic_model_creator(DouyuBarrage, name="DouyuBarrage")
