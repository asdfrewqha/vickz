from typing import Annotated, Optional

from app.database.models import User
from app.dependencies.checks import check_user_token
from app.dependencies.responses import okresponse
from fastapi import APIRouter, Cookie, Depends, status

router = APIRouter()


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    user: Annotated[User, Depends(check_user_token)],
    access_token: Annotated[Optional[str], Cookie()] = None,
    refresh_token: Annotated[Optional[str], Cookie()] = None,
):
    response = okresponse()
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response
