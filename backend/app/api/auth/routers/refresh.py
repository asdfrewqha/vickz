from typing import Annotated

from fastapi import APIRouter, Response, Depends, status

from app.database.models import User
from app.dependencies.responses import okresponse
from app.dependencies.checks import check_refresh
from app.utils.token_manager import TokenManager
from app.core.logging import get_logger

logger = get_logger()


router = APIRouter()


@router.get("/refresh", status_code=status.HTTP_200_OK)
async def refresh(response: Response, user: Annotated[User, Depends(check_refresh)]):
    response.set_cookie("access_token", TokenManager.create_token(
        {"sub": str(user.id), "type": "access"},
        TokenManager.ACCESS_TOKEN_EXPIRE_MINUTES,
    ))
    return okresponse()
