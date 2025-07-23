from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.checks import check_user_token
from app.api.user.schemas import UserProfileResponse
from app.database.models import User


router = APIRouter()


@router.get("/profile", response_model=UserProfileResponse)
async def profile(user: Annotated[User, Depends(check_user_token)]):
    return UserProfileResponse.model_validate(user, from_attributes=True)
