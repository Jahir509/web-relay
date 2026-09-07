async def create(conn, url, secret, event_types):
    return await conn.fetchrow(
        """insert into endpoints (url, secret, event_types)
           values ($1, $2, $3)
           returning id, url, secret, event_types""",
        url,
        secret,
        event_types,
    )


async def get_first_id(conn):
    return await conn.fetchval("select id from endpoints limit 1")
