"""Address Book API.

A minimal FastAPI application for creating, updating, deleting, and
geo-searching addresses, backed by SQLite.
"""

from __future__ import annotations

import logging

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.database import Base, engine, get_db
from app.schemas import AddressCreate, AddressOut, AddressUpdate, AddressWithDistance

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Create tables on startup. For a real production service this would be
# replaced by a migration tool (e.g. Alembic), but a simple create_all is
# sufficient for this exercise.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Address Book API",
    description="Create, update, delete, and geo-search addresses.",
    version="1.0.0",
)


def get_address_or_404(address_id: int, db: Session = Depends(get_db)):
    address = crud.get_address(db, address_id)
    if address is None:
        logger.warning("Address id=%s not found", address_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    return address


@app.post("/addresses", response_model=AddressOut, status_code=status.HTTP_201_CREATED)
def create_address(payload: AddressCreate, db: Session = Depends(get_db)):
    """Create a new address."""
    return crud.create_address(db, payload)


@app.get("/addresses", response_model=list[AddressOut])
def list_addresses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List addresses (paginated)."""
    return crud.list_addresses(db, skip=skip, limit=limit)


@app.get("/addresses/nearby", response_model=list[AddressWithDistance])
def search_nearby(
    latitude: float = Query(..., ge=-90, le=90, description="Center point latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Center point longitude"),
    radius_km: float = Query(..., gt=0, le=20037.5, description="Search radius in kilometers"),
    db: Session = Depends(get_db),
):
    """Return addresses within `radius_km` of the given coordinates, nearest first.

    NOTE: this route is declared before `/addresses/{address_id}` so that the
    literal path `/addresses/nearby` isn't swallowed by the `{address_id}`
    path parameter.
    """
    results = crud.search_nearby(db, latitude, longitude, radius_km)
    return [
        AddressWithDistance.model_validate(
            {**AddressOut.model_validate(address).model_dump(), "distance_km": round(distance, 3)}
        )
        for address, distance in results
    ]


@app.get("/addresses/{address_id}", response_model=AddressOut)
def get_address(address=Depends(get_address_or_404)):
    """Retrieve a single address by id."""
    return address


@app.put("/addresses/{address_id}", response_model=AddressOut)
def update_address(payload: AddressUpdate, address=Depends(get_address_or_404), db: Session = Depends(get_db)):
    """Partially update an existing address."""
    return crud.update_address(db, address, payload)


@app.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address=Depends(get_address_or_404), db: Session = Depends(get_db)):
    """Delete an address."""
    crud.delete_address(db, address)
    return None
