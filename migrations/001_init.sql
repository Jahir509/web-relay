create table messages (
    id          uuid primary key default gen_random_uuid(),
    event_type  text not null,
    payload     jsonb not null,
    created_at  timestamptz not null default now()
);

create table endpoints (
    id          uuid primary key default gen_random_uuid(),
    url         text not null unique,
    secret      text not null,
    created_at  timestamptz not null default now()
);

create table deliveries (
    id              uuid primary key default gen_random_uuid(),
    message_id      uuid not null references messages (id) on delete cascade,
    endpoint_id     uuid not null references endpoints (id) on delete cascade,
    status          text not null default 'pending'
                    check (status in ('pending', 'delivered', 'dead')),
    attempt_count   integer not null default 0,
    next_attempt_at timestamptz not null default now(),
    created_at      timestamptz not null default now()
);

create index deliveries_due_idx on deliveries (next_attempt_at)
    where status = 'pending';
