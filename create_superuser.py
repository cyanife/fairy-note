import asyncio

from tortoise import Tortoise

from fairy_note.auth import get_password_hash
from fairy_note.models import UserModel
from fairy_note.settings import TORTOISE_ORM


async def create_superuser():
    await Tortoise.init(config=TORTOISE_ORM)
    user = UserModel()
    user.username = "admin"
    user.hashed_password = get_password_hash("admin")
    user.is_active = True
    await user.save()


if __name__ == "__main__":
    asyncio.run(create_superuser())
