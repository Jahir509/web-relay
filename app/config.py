import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://relay:relay@localhost:5432/relay")
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "1"))
FAST_RETRY = os.getenv("FAST_RETRY") == "1"

# Secret the test receiver in routers/sink.py verifies with.
SINK_SECRET = os.getenv("SINK_SECRET", "whsec_tyHud0SZfHTqj6LMdH5kku-43NPBuzKnKJxhuyrHKu8")

# How long a signed request stays valid, in seconds.
SIGNATURE_TOLERANCE = 300

RETRY_SCHEDULE = (
    [timedelta(seconds=s) for s in (1, 2, 4, 6, 8, 10, 12)]
    if FAST_RETRY
    else [
        timedelta(seconds=10),
        timedelta(seconds=30),
        timedelta(minutes=2),
        timedelta(minutes=10),
        timedelta(hours=1),
        timedelta(hours=3),
        timedelta(hours=24),
    ]
)
