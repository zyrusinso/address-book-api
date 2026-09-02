"""Pydantic request/response schemas, including field validation."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AddressBase(BaseModel):
    """Fields shared by create/update payloads."""

    street: str = Field(..., min_length=1, max_length=255, examples=["123 Main St"])
    city: str = Field(..., min_length=1, max_length=120, examples=["Springfield"])
    state: str | None = Field(None, max_length=120, examples=["IL"])
    postal_code: str | None = Field(None, max_length=20, examples=["62701"])
    country: str = Field(..., min_length=1, max_length=120, examples=["USA"])

    # Real-world latitude/longitude bounds are enforced directly via `ge`/`le`.
    latitude: float = Field(..., ge=-90, le=90, examples=[39.7817])
    longitude: float = Field(..., ge=-180, le=180, examples=[-89.6501])

    @field_validator("street", "city", "country")
    @classmethod
    def not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class AddressCreate(AddressBase):
    """Payload for creating a new address."""


class AddressUpdate(BaseModel):
    """Payload for partially updating an existing address.

    All fields are optional; only the ones supplied are changed. The same
    bounds/validation as `AddressBase` apply to any field that is provided.
    """

    street: str | None = Field(None, min_length=1, max_length=255)
    city: str | None = Field(None, min_length=1, max_length=120)
    state: str | None = Field(None, max_length=120)
    postal_code: str | None = Field(None, max_length=20)
    country: str | None = Field(None, min_length=1, max_length=120)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)

    @field_validator("street", "city", "country")
    @classmethod
    def not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class AddressOut(AddressBase):
    """Address as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class AddressWithDistance(AddressOut):
    """Address returned by the proximity search, including its distance."""

    distance_km: float
