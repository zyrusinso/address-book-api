"""Database access layer: all read/write operations against `Address`."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.geo import bounding_box, haversine_km
from app.models import Address
from app.schemas import AddressCreate, AddressUpdate

logger = logging.getLogger(__name__)


def create_address(db: Session, payload: AddressCreate) -> Address:
    address = Address(**payload.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    logger.info("Created address id=%s city=%s", address.id, address.city)
    return address


def get_address(db: Session, address_id: int) -> Address | None:
    return db.get(Address, address_id)


def list_addresses(db: Session, skip: int = 0, limit: int = 100) -> list[Address]:
    stmt = select(Address).order_by(Address.id).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def update_address(db: Session, address: Address, payload: AddressUpdate) -> Address:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(address, field, value)
    db.commit()
    db.refresh(address)
    logger.info("Updated address id=%s fields=%s", address.id, list(updates))
    return address


def delete_address(db: Session, address: Address) -> None:
    db.delete(address)
    db.commit()
    logger.info("Deleted address id=%s", address.id)


def search_nearby(
    db: Session, lat: float, lon: float, radius_km: float
) -> list[tuple[Address, float]]:
    """Return addresses within `radius_km` of (lat, lon), nearest first.

    A SQL bounding-box filter narrows the candidate set first, then an exact
    haversine distance is computed in Python for each candidate and used to
    apply the precise radius cutoff and sort order.
    """
    min_lat, max_lat, min_lon, max_lon = bounding_box(lat, lon, radius_km)

    stmt = select(Address).where(
        Address.latitude.between(min_lat, max_lat),
        Address.longitude.between(min_lon, max_lon),
    )
    candidates = db.scalars(stmt).all()

    results = [
        (address, haversine_km(lat, lon, address.latitude, address.longitude))
        for address in candidates
    ]
    within_radius = [pair for pair in results if pair[1] <= radius_km]
    within_radius.sort(key=lambda pair: pair[1])

    logger.info(
        "Nearby search lat=%s lon=%s radius_km=%s -> %d result(s)",
        lat,
        lon,
        radius_km,
        len(within_radius),
    )
    return within_radius
