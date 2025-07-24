from app.utils.s3_adapter import S3HttpxSigV4Adapter
from fastapi import Request


async def get_s3_b1(request: Request) -> S3HttpxSigV4Adapter:
    return request.app.state.s3_b1


async def get_s3_b2(request: Request) -> S3HttpxSigV4Adapter:
    return request.app.state.s3_b2
