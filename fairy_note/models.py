from typing import Optional

from pydantic import EmailStr
from tortoise import fields, models

from .settings import BARRAGE_TABLE_NAME

# from .auth import get_password_hash


class UserModel(models.Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(index=True, unique=True, null=False, max_length=255)
    hashed_password = fields.CharField(null=False, max_length=255)
    is_active = fields.BooleanField(default=True, null=False)

    # async def to_dict(self):
    #     d = {}
    #     for field in self._meta.db_fields:
    #         d[field] = getattr(self, field)
    #     for field in self._meta.backward_fk_fields:
    #         d[field] = await getattr(self, field).all().values()
    #     return d

    # @classmethod
    # def create(cls, **kwargs):
    #     kwargs["hashed_password"] = get_password_hash(kwargs["password"])
    #     return super().create(**kwargs)

    # @classmethod
    # async def get_user_by_name(cls, username: str):
    #     return await cls.get(username=username)

    class Meta:
        table = "user"

    class PydanticMeta:
        exclude = ["hashed_password"]


class DouyuBarrage(models.Model):

    id = fields.IntField(pk=True)
    userid = fields.CharField(max_length=20)
    nickname = fields.CharField(max_length=100)
    time = fields.DatetimeField()

    chatmsg = fields.JSONField()

    class Meta:
        table = BARRAGE_TABLE_NAME
