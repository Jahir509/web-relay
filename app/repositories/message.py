async def create(conn, event_type, payload):
    return await conn.fetchrow(
        """insert into messages (event_type, payload)
           values ($1, $2)
           returning id, event_type""",
        event_type,
        payload,
    )


async def get(conn, message_id):
    return await conn.fetchrow(
        "select id, event_type, payload from messages where id = $1",
        message_id,
    )
