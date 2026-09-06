import json
from typing import Annotated

from asyncpg import Connection, create_pool
from fastapi import Depends

from app.config import DATABASE_URL

_pool = None


async def init_connection(conn):
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def connect():
    global _pool
    _pool = await create_pool(DATABASE_URL, init=init_connection)


async def disconnect():
    await _pool.close()


def acquire():
    """For code outside a request, like the dispatcher loop."""
    return _pool.acquire()


async def get_conn():
    async with _pool.acquire() as conn:
        yield conn


Conn = Annotated[Connection, Depends(get_conn)]
