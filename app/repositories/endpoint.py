async def create(conn, url, secret):
    return await conn.fetchrow(
        """insert into endpoints (url, secret)
           values ($1, $2)
           returning id, url, secret""",
        url,
        secret,
    )


async def get_first_id(conn):
    return await conn.fetchval("select id from endpoints limit 1")
