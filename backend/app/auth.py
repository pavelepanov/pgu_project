import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import User


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict:
    if not init_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Telegram initData")
    if not bot_token:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="BOT_TOKEN is not configured")

    data = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = data.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Telegram hash is missing")

    check_string = "\n".join(f"{key}={value}" for key, value in sorted(data.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram signature")

    if "user" in data:
        try:
            data["user"] = json.loads(data["user"])
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram user payload") from exc

    return data


def _ensure_fresh_auth(data: dict) -> None:
    settings = get_settings()
    if settings.is_local:
        return

    auth_date = data.get("auth_date")
    if not auth_date:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Telegram auth_date is missing")

    try:
        auth_timestamp = int(auth_date)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram auth_date") from exc

    if time.time() - auth_timestamp > settings.init_data_max_age_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Telegram initData expired")


def get_current_user(
    db: Session = Depends(get_db),
    x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
    x_dev_user: str | None = Header(default=None, alias="X-Dev-User"),
) -> User:
    settings = get_settings()

    if settings.is_local and x_dev_user == "true":
        telegram_user = {
            "id": settings.dev_telegram_user_id,
            "first_name": settings.dev_telegram_first_name,
            "last_name": "",
            "username": "dev_user",
            "photo_url": None,
        }
    else:
        data = validate_telegram_init_data(x_telegram_init_data or "", settings.bot_token)
        _ensure_fresh_auth(data)
        telegram_user = data.get("user")
        if not telegram_user or "id" not in telegram_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Telegram user is missing")

    from app.crud import upsert_user_from_telegram

    return upsert_user_from_telegram(db, telegram_user)
