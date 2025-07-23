from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from itsdangerous import BadSignature
from itsdangerous.url_safe import URLSafeTimedSerializer

from app.api.auth.schemas import EditPwdRequest
from app.api.auth.utils import get_password_hash, verify_password
from app.dependencies.responses import okresponse
from app.database.adapter import adapter
from app.database.models import User
from app.database.session import get_async_session


router = APIRouter()


@router.put("/change-password")
async def edit_pwd_confirm(code: str, password: EditPwdRequest, session: Annotated[AsyncSession, Depends(get_async_session)]):
    serializer = URLSafeTimedSerializer()
    try:
        user_id = serializer.loads(code, max_age=600)
    except BadSignature:
        raise HTTPException(403, "Code is invalid or has expired")
    user = await adapter.get_by_id(User, user_id)
    if not user:
        raise HTTPException(404, "User with this token does not exist")
    if verify_password(password.password, user.password_hash):
        raise HTTPException(400, "Your password is the same with the old one")
    password_hash = get_password_hash(password=password.password)
    await adapter.update_by_id(User, user_id, {"password_hash": password_hash}, session=session)
    return okresponse("Password changed succesfully")
