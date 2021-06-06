from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise

from .exceptions import exception_handler
from .routers import init_app
from .settings import TORTOISE_ORM


def get_app():
    app = FastAPI(title="fairy's note")
    register_tortoise(app, config=TORTOISE_ORM)
    app.add_exception_handler(HTTPException, exception_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex="http://localhost.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    init_app(app)

    return app
