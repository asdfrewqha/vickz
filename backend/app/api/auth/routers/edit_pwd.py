import dns.resolver
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from itsdangerous.url_safe import URLSafeTimedSerializer

from app.api.auth.tasks import send_confirmation_email_pwd
from app.core.logging import get_logger
from app.core.settings import settings
from app.dependencies.responses import okresponse
from app.database.adapter import adapter
from app.database.models import User


router = APIRouter()
logger = get_logger()


@router.post("/change-password")
async def change_pwd(email: str):
    user = await adapter.get_by_value(User, "email", email)
    if not user:
        raise HTTPException(404, "User not found")
    user = user[0]
    email_domain = email.split("@")[1]
    try:
        records = dns.resolver.resolve(email_domain, "MX")
        mxRecord = records[0].exchange
        mxRecord = str(mxRecord)
    except Exception:
        raise HTTPException(403, "Email is not valid")
    serializer = URLSafeTimedSerializer(secret_key=settings.jwt_settings.jwt_secret_key.get_secret_value())
    payld = serializer.dumps(str(user.id))
    send_confirmation_email_pwd.delay(email, payld)
    return okresponse
