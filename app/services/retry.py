import random

from app.config import RETRY_SCHEDULE
from app.models.delivery import Outcome


def classify(status_code):
    if status_code in (408, 429) or 500 <= status_code < 600:
        return Outcome.PENDING
    elif 200 <= status_code < 300:
        return Outcome.DELIVERED
    else:
        return Outcome.DEAD


def next_interval(attempt_count):
    """How long to wait before the next attempt. None once the schedule runs out."""
    if attempt_count >= len(RETRY_SCHEDULE):
        return None
    return RETRY_SCHEDULE[attempt_count] * random.uniform(0.8, 1.2)
