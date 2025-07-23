from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import JWTError, jwt
from fastapi.exceptions import HTTPException

from app.core.settings import settings
from app.core.logging import get_logger

logger = get_logger()


class TokenManager:
    SECRET_KEY = settings.jwt_settings.jwt_secret_key.get_secret_value()
    ALGORITHM = settings.jwt_settings.jwt_algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_settings.access_token_expire_min

    @staticmethod
    def create_token(data: Dict[str, Any], access: bool = True) -> str:
        to_encode = data.copy()
        if access:
            expire = datetime.now(timezone.utc) + timedelta(minutes=TokenManager.ACCESS_TOKEN_EXPIRE_MINUTES)
            to_encode.update({"exp": expire})
            to_encode.update({"type": "access"})
        else:
            to_encode.update({"type": "refresh"})
        encoded_jwt = jwt.encode(
            to_encode,
            TokenManager.SECRET_KEY,
            algorithm=TokenManager.ALGORITHM,
        )
        return encoded_jwt

    @staticmethod
    def decode_token(token: str, access: bool = True) -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                TokenManager.SECRET_KEY,
                algorithms=[TokenManager.ALGORITHM],
            )
            if not payload:
                logger.info("No token data")
                raise HTTPException(401, "No token data")
            type = "access" if access else "refresh"
            if payload.get("type") != type:
                logger.info("Invalid token type")
                raise HTTPException(401, "Invalid token type")
            if access:
                if payload.get("exp"):
                    if datetime.fromtimestamp(payload.get("exp"), timezone.utc) < datetime.now(timezone.utc):
                        logger.info("Token has expired")
                        raise HTTPException(401, "Token has expired")
                else:
                    raise HTTPException(401, "Invalid token")
            return payload
        except JWTError:
            raise HTTPException(401, "Invalid token")
