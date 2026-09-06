async def create(conn, message_id, endpoint_id):
    await conn.execute(
        "insert into deliveries (message_id, endpoint_id) values ($1, $2)",
        message_id,
        endpoint_id,
    )


async def fan_out(conn, message_id):
    return await conn.fetch(
        """insert into deliveries (message_id, endpoint_id)
           select $1, id from endpoints
           returning id""",
        message_id,
    )


async def get_due(conn, limit=10):
    return await conn.fetch(
        """select d.id, m.event_type, m.payload, d.attempt_count, e.url, e.secret
           from deliveries d
           join messages m on m.id = d.message_id
           join endpoints e on e.id = d.endpoint_id
           where d.status = 'pending' and d.next_attempt_at <= now()
           order by d.next_attempt_at
           for update of d skip locked
           limit $1""",
        limit,
    )


async def record_attempt(conn, delivery_id, status, interval, attempt_count, result):
    async with conn.transaction():
        await conn.execute(
            """update deliveries
                set attempt_count = attempt_count + 1,
                    next_attempt_at = now() + $3,
                    status = $2
                where id = $1""",
            delivery_id,
            status,
            interval,
        )

        await conn.execute(
            """insert into delivery_attempts
                (delivery_id, attempt_number, response_body, response_status, error, duration_ms)
                values ($1, $2, $3, $4, $5, $6)""",
            delivery_id,
            attempt_count,
            result["response_body"],
            result["response_status"],
            result["error"],
            result["duration_ms"],
        )



async def list_by_status(conn, status):
    return await conn.fetch(
        """select d.id, m.event_type, m.payload, d.attempt_count, d.status, d.next_attempt_at
           from deliveries d
           join messages m on m.id = d.message_id
           where d.status = $1""",
        status,
    )


async def replay_dead(conn, endpoint_id):
    return await conn.fetch(
        """update deliveries
           set status = 'pending', attempt_count = 0, next_attempt_at = now()
           where status = 'dead' and endpoint_id = $1
           returning id""",
        endpoint_id,
    )
