# Webhook Relay

Reliable webhook delivery as a service. Hand it an event; it makes sure the event
reaches every subscriber — retrying through outages, refusing to retry what will
never succeed, and keeping a replayable record of everything that failed.

![Architecture](docs/architecture.svg)

---

## The problem

<!--
WRITE THIS YOURSELF — 3-4 sentences. The argument you should make:

  Two HTTP requests have different lifespans. The producer's request has to
  finish in milliseconds (a customer is waiting on a checkout page). A delivery
  to a subscriber whose server is down might take an hour. You cannot fit an
  hour of work inside 200 milliseconds.

  Then the consequences: a slow receiver makes the producer slow; three
  subscribers means three sequential HTTP calls in the request path; if the
  process crashes there is no record of what wasn't sent.

  Close with: the database row is the bridge between the two lifespans.

Say it in your own words. If you can say this out loud in an interview without
notes, the project has done its job.
-->

## Quickstart

```bash
git clone <repo-url> && cd webhook-relay
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

createdb relay                      # or: psql -c "create database relay"
psql -d relay -f migrations/001_init.sql

export DATABASE_URL=postgresql://relay:relay@localhost:5432/relay
uvicorn app.main:app --reload
```

Interactive docs at `http://localhost:8000/docs`.

Register a subscriber and publish an event:

```bash
curl -X POST http://localhost:8000/endpoints \
  -H "Content-Type: application/json" \
  -d '{"url": "http://localhost:8000/sink"}'
# -> returns the signing secret, shown once

curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{"event_type": "order.paid", "payload": {"order_id": 4471, "amount": 2500}}'
# -> 202 Accepted
```

Set `FAST_RETRY=1` to compress the retry schedule to seconds for local testing.

---

## How it works

A producer publishes an event. The ingest API writes one `messages` row and one
`deliveries` row per registered subscriber — **in a single transaction** — then
returns `202`. Nothing has been delivered yet; what has been promised is
durability.

A background loop polls for due deliveries, signs each request with that
subscriber's secret, sends it, and records the outcome. Success is terminal.
A retryable failure schedules the next attempt further out. A permanent failure
goes straight to the dead-letter queue.

### Data model

| Table | One row per | Holds |
|---|---|---|
| `messages` | published event | `event_type`, `payload` |
| `deliveries` | message × endpoint | `status`, `attempt_count`, `next_attempt_at` |
| `delivery_attempts` | individual HTTP try | status code, response body, error, duration |
| `endpoints` | subscriber | `url`, signing `secret` |

<!--
WRITE THIS YOURSELF — two short paragraphs explaining the splits:

  1. Why messages and deliveries are separate tables.
     (One event fans out to N subscribers, each retrying on its own clock. A
     vendor whose server is down must not hold up the courier.)

  2. Why deliveries and delivery_attempts are separate.
     (A delivery has one current status but may have eight attempts behind it.
     Flatten them and you either lose the history or overwrite the same row
     eight times with no record of what each response was.)
-->

### Retry schedule

| Attempt | Delay | Cumulative |
|---|---|---|
| 1 | immediate | 0 |
| 2 | 10s | 10s |
| 3 | 30s | 40s |
| 4 | 2m | ~3m |
| 5 | 10m | ~13m |
| 6 | 1h | ~1h |
| 7 | 3h | ~4h |
| 8 | 24h | ~28h |

Each delay carries ±20% jitter. After the last attempt the delivery is
dead-lettered.

---

## Walkthrough: one event, three subscribers

<!--
PASTE YOUR OWN OUTPUT HERE — the fan-out test from `deliveries`:
one message_id, three delivery rows, one `delivered` and two `dead`.

Then two sentences underneath. The point to make: the healthy subscriber was
delivered in 4ms and did NOT wait for the two failing ones; and the two failing
ones retried on independent clocks (look at the interleaved timestamps in
delivery_attempts — jitter kept them from firing in lockstep).
-->

```
paste the deliveries query output here
```

## Walkthrough: failure and recovery

<!--
PASTE YOUR OWN OUTPUT HERE — the three JSON responses from the replay test:

  1. GET /deliveries?status=dead      -> count: 2, attempt_count: 1
  2. POST /endpoints/{id}/replay      -> {"replayed": 2}
  3. GET /deliveries?status=delivered -> count: 2

Then one sentence naming what the reader should notice: attempt_count is 1,
not 8 — a 401 is not retried, because retrying an identical request against an
identical wrong key would produce an identical result. The operator fixes the
key, then replays.
-->

```
paste the three responses here
```

## Walkthrough: three kinds of failure

<!--
PASTE YOUR OWN OUTPUT HERE — the delivery_attempts rows showing:

  - a 401:  response_status = 401, error null, body "invalid signature"
  - a refused connection: response_status null, error "All connection attempts failed"
  - a success: 200 with a body

One sentence: before this table existed all three looked identical from the
outside (`status = dead, attempt_count = 1`).
-->

```
paste the delivery_attempts rows here
```

---

## Design decisions

<!--
THIS IS THE SECTION INTERVIEWERS READ CLOSELY. Write each one as a short
paragraph: what you chose, why, and what would change your mind.

The four worth writing up, with the argument you already know:
-->

### Postgres as the queue, not a broker

<!--
  - Transactional: the event and its delivery rows commit together. With a
    broker you'd have a dual-write problem — Postgres commits, the publish
    fails, the event is gone. The standard fix for that is an outbox table;
    and if you need an outbox table anyway, making it the queue directly
    removes a moving part.
  - Legible: retry scheduling is a column, so "what is due and why" is a query
    anyone can run. In a broker it needs a delayed-message plugin and its own
    tooling.
  - Name the ceiling honestly: a few thousand deliveries per second, and
    ~500ms polling latency. Past that a broker is the right answer — but on
    measurement, not upfront.
-->

### 4xx is not retried; 5xx, 429, 408 and network errors are

<!--
  Retry means sending an identical request again. So the question is whether
  the same request, a little later, could produce a different result — and
  since your side hasn't changed, that requires the receiver's state to change.

  5xx generally resolves on its own (a deploy finishes, a database comes back).
  4xx requires a human (fix the URL, rotate the key back). Silently retrying a
  404 for 28 hours burns both sides' resources and tells nobody.

  429 is the exception that proves the rule — "slow down" is temporary.
-->

### Signatures cover raw bytes, not parsed objects

<!--
  json.dumps produces {"a": 1}; httpx produces {"a":1}. Two spaces, and the
  hash is completely different. So the sender must sign exactly the bytes it
  puts on the wire (content=, not json=) and the receiver must verify against
  await request.body(), not a parsed dict.

  Also worth a line: the timestamp is inside the signature, so an attacker
  can't replay a captured-but-valid request; and compare_digest is used rather
  than == because == leaks how many characters matched via timing.
-->

### Secrets are stored reversibly, unlike passwords

<!--
  Verifying a password doesn't need the original, so it can be hashed.
  Producing an HMAC signature does need the original, so the secret must be
  recoverable. Production answer: encrypt the column (pgcrypto or
  application-level) so a database dump doesn't leak signing keys.
-->

---

## API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/events` | Publish an event → `202`, fans out to all subscribers |
| `GET` | `/events/{id}` | Fetch one event |
| `POST` | `/endpoints` | Register a subscriber; returns the secret once |
| `GET` | `/deliveries?status=` | List deliveries by status — the dead-letter view |
| `POST` | `/endpoints/{id}/replay` | Reset this endpoint's dead deliveries and redeliver |
| `GET` | `/health` | Liveness |

## Project structure

```
app/
├── main.py              app creation, lifespan, router registration
├── config.py            env-driven settings
├── db.py                connection pool, get_conn dependency
├── models/              pydantic request/response schemas
├── routers/             HTTP layer — no SQL
├── services/            dispatcher loop, signing, retry policy
└── repositories/        all SQL
migrations/
└── 001_init.sql
```

Routers speak HTTP, services hold the rules, repositories hold the SQL, and none
of them knows the others' job.

---

## Not yet built

<!--
Keep this section. It is not a weakness — a candidate who knows the edges of
their own system reads as more senior than one who implies it's finished.

Write each as: what's missing, and the concrete consequence.
-->

- **Circuit breaker** — a permanently dead endpoint keeps consuming dispatcher
  time on every cycle. A `consecutive_failures` counter on `endpoints` that
  auto-disables after a threshold would stop one dead subscriber from slowing
  down everyone else.
- **Event-type filtering** — every subscriber currently receives every event.
  An `event_types` array on `endpoints` (empty meaning wildcard) is the next
  step.
- **Multi-tenancy** — a single `app_id` scope, no authentication on the ingest
  API.
- **Metrics** — structured logs only; no Prometheus counters for delivery rate,
  queue depth, or attempt latency.
- **Load testing** — the throughput ceiling above is reasoned, not measured.

<!--
Add anything else you know is missing. Being first to name a gap is much
stronger than having an interviewer find it.
-->