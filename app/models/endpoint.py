from uuid import UUID

from pydantic import BaseModel


class EndpointIn(BaseModel):
    url: str


class EndpointOut(BaseModel):
    id: UUID
    url: str
    secret: str
