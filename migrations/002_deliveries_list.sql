create table delivery_attempts (
    id bigserial not null primary key,
    delivery_id uuid not null references deliveries(id) on delete cascade,
    attempt_number integer not null,
    response_body text,
    response_status integer,
    error text,
    duration_ms integer,
    created_at timestamptz not null default now()
);

create index delivery_attempts_delivery_idx
    on delivery_attempts (delivery_id, attempt_number);


alter table endpoints add column event_types text[] not null default '{}';