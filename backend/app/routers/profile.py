from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app.auth import get_current_user
from app.db import get_db
from app.models import User

router = APIRouter(prefix="/api", tags=["profile"])


@router.get("/profile")
def read_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.get_profile(db, current_user)
