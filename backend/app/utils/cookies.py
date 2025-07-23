from fastapi import Cookie
from fastapi.exceptions import HTTPException
from typing import Annotated, Dict, Literal


def get_tokens_cookies(
    access_token: Annotated[str | None, Cookie()] = None,
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> Dict[Literal["access", "refresh"], str]:
    if not access_token or not refresh_token:
        raise HTTPException(status_code=401, detail="Missing tokens")

    return {
        "access": access_token,
        "refresh": refresh_token,
    }
