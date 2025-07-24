import mimetypes
from typing import Annotated
from uuid import UUID

import requests
from app.database.adapter import adapter
from app.database.models import User, Video, View
from app.database.session import get_async_session
from app.dependencies.checks import check_user_token
from app.dependencies.responses import badresponse
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/stream-video/{uuid}", response_class=StreamingResponse)
async def stream_by_uuid(
    uuid: UUID,
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    video = await adapter.get_by_id(Video, uuid, session=session)
    if not video:
        raise HTTPException(404, "Video not found")

    mime_type, _ = mimetypes.guess_type(video.url)
    if not mime_type:
        mime_type = "application/octet-stream"

    r = requests.get(video.url, stream=True)

    if r.status_code not in (200, 206):
        return badresponse("Media not accessible", r.status_code)

    view = await adapter.get_by_values(
        View, {"user_id": user.id, "video_id": uuid}, session=session
    )
    if not view:
        await adapter.insert(View, {"user_id": user.id, "video_id": uuid}, session=session)
        views = video.views + 1
        await adapter.update_by_id(Video, uuid, {"views": views}, session=session)

    response_headers = {
        "Content-Length": r.headers.get("Content-Length", ""),
        "Content-Range": r.headers.get("Content-Range", ""),
        "Accept-Ranges": r.headers.get(
            "Accept-Ranges",
            "bytes" if mime_type.startswith("video/") else "none",
        ),
    }

    return StreamingResponse(
        r.iter_content(chunk_size=8192),
        status_code=r.status_code,
        media_type=mime_type,
        headers={k: v for k, v in response_headers.items() if v},
    )
