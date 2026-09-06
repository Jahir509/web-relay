import hashlib
import hmac


def sign(secret, timestamp, body):
    return hmac.new(
        secret.encode(),
        f"{timestamp}.".encode() + body,
        hashlib.sha256,
    ).hexdigest()


def verify(secret, timestamp, body, signature):
    return hmac.compare_digest(sign(secret, timestamp, body), signature)
