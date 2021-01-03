import asyncio

from fairy_note.models import UserCreate
from fairy_note.routers import fastapi_users


async def create_superuser():
    await fastapi_users.create_user(
        UserCreate(
            email="admin@fairynote.live",
            password="password",
            is_superuser=True,
        )
    )


if __name__ == "__main__":
    asyncio.run(create_superuser())
