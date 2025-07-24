from typing import Annotated

from app.api.user.utils import process_image
from app.core.logging import get_logger
from app.core.settings import settings
from app.database.adapter import adapter
from app.database.models import User
from app.database.session import get_async_session
from app.dependencies.checks import check_user_token
from app.dependencies.responses import badresponse, emptyresponse, okresponse
from app.dependencies.s3_buckets import get_s3_b1
from app.utils.s3_adapter import S3HttpxSigV4Adapter
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger()

router = APIRouter()


@router.put("/profile-picture")
async def updt_pfp(
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    s3: Annotated[S3HttpxSigV4Adapter, Depends(get_s3_b1)],
    file: UploadFile = File(...),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(415, "Unsupported file")
    filename = f"avatar_{user.id}.png"
    if user.avatar_url != settings.default_avatar_url:
        try:
            await s3.delete_file(filename)
        except Exception as e:
            return badresponse(f"Failed to remove old avatar: {e}", 500)
    buffer = process_image(file)
    await s3.upload_file(buffer, filename)
    public_url = s3.get_url(filename)
    await adapter.update_by_id(User, user.id, {"avatar_url": public_url}, session=session)

    return okresponse()


@router.delete("/profile-picture", status_code=204)
async def del_pfp(
    user: Annotated[User, Depends(check_user_token)],
    s3: Annotated[S3HttpxSigV4Adapter, Depends(get_s3_b1)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    if user.avatar_url == settings.default_avatar_url:
        return badresponse("Not found", 404)

    filename = f"avatar_{user.id}.png"

    try:
        await s3.delete_file(filename)
        await adapter.update_by_id(
            User, user.id, {"avatar_url": settings.default_avatar_url}, session=session
        )
    except Exception as e:
        logger.error(f"Error deleting profile picture: {e}")
        return badresponse(f"Error deleting old avatar: {e}", 500)

    return emptyresponse
