import io
import aiofiles
from typing import Union, AsyncIterator, List, Tuple
from urllib.parse import quote

import httpx
from httpx_aws_auth import AwsCredentials, AwsSigV4Auth

from app.core.settings import settings
from app.core.logging import get_logger

logger = get_logger()


class S3HttpxSigV4Adapter:
    PART_SIZE = 5 * 1024 * 1024

    def __init__(self, bucket: str, region: str = "ru-1"):
        self.bucket = bucket
        self.endpoint_url = settings.s3_settings.endpoint_url.rstrip("/")
        creds = AwsCredentials(
            access_key=settings.s3_settings.access_key,
            secret_key=settings.s3_settings.secret_key.get_secret_value()
        )
        self.auth = AwsSigV4Auth(credentials=creds, region=region, service="s3")
        self.client = httpx.AsyncClient(
            auth=self.auth,
            timeout=httpx.Timeout(600.0, connect=10.0, read=600.0)
        )

    async def _stream_file_parts(self, path: str) -> AsyncIterator[bytes]:
        async with aiofiles.open(path, "rb") as f:
            while True:
                chunk = await f.read(self.PART_SIZE)
                if not chunk:
                    break
                yield chunk

    async def _init_multipart_upload(self, object_name: str) -> str:
        url = f"{self.endpoint_url}/{self.bucket}/{object_name}?uploads"
        resp = await self.client.post(url)
        try:
            resp.raise_for_status()
        except Exception:
            logger.error(f"Init multipart upload failed: {resp.status_code} {resp.text}")
            raise
        from xml.etree import ElementTree as ET
        root = ET.fromstring(resp.text)
        upload_id = root.find(".//{http://s3.amazonaws.com/doc/2006-03-01/}UploadId")
        if upload_id is None:
            logger.error(f"UploadId not found in response: {resp.text}")
            raise RuntimeError("Failed to get uploadId")
        return upload_id.text

    async def _upload_part(self, object_name: str, upload_id: str, part_number: int, data: bytes) -> str:
        url = f"{self.endpoint_url}/{self.bucket}/{object_name}?partNumber={part_number}&uploadId={upload_id}"
        resp = await self.client.put(url, content=data)
        resp.raise_for_status()
        etag = resp.headers.get("etag")
        if not etag:
            raise RuntimeError(f"Part {part_number} upload response missing ETag")
        return etag.strip('"')

    async def _complete_multipart_upload(self, object_name: str, upload_id: str, parts: List[Tuple[int, str]]):
        url = f"{self.endpoint_url}/{self.bucket}/{object_name}?uploadId={upload_id}"
        parts_xml = "".join(
            f"<Part><PartNumber>{num}</PartNumber><ETag>\"{etag}\"</ETag></Part>"
            for num, etag in parts
        )
        body = f"<CompleteMultipartUpload>{parts_xml}</CompleteMultipartUpload>"

        headers = {"Content-Type": "application/xml"}
        resp = await self.client.post(url, content=body.encode("utf-8"), headers=headers)
        resp.raise_for_status()

    async def upload_file_multipart(self, file_path: str, object_name: str, public: bool = True):
        upload_id = await self._init_multipart_upload(object_name)

        parts: List[Tuple[int, str]] = []
        part_number = 1

        async for chunk in self._stream_file_parts(file_path):
            etag = await self._upload_part(object_name, upload_id, part_number, chunk)
            parts.append((part_number, etag))
            part_number += 1

        await self._complete_multipart_upload(object_name, upload_id, parts)

        if public:
            url = f"{self.endpoint_url}/{self.bucket}/{object_name}?acl"
            headers = {"x-amz-acl": "public-read"}
            resp = await self.client.put(url, headers=headers)
            resp.raise_for_status()

        return f"{self.endpoint_url}/{self.bucket}/{object_name}"

    async def upload_file(
        self,
        file_data: Union[str, bytes, io.BytesIO],
        object_name: str,
        public: bool = True,
    ):
        try:
            headers = {}
            if public:
                headers["x-amz-acl"] = "public-read"

            url = f"{self.endpoint_url}/{self.bucket}/{object_name}"

            # Потоковая отправка — если путь
            if isinstance(file_data, str):
                content = self._stream_file(file_data)
            # если BytesIO или bytes — в память (мелкие файлы)
            elif isinstance(file_data, io.BytesIO):
                file_data.seek(0)
                content = file_data.read()
            elif isinstance(file_data, bytes):
                content = file_data
            else:
                raise TypeError(f"Unsupported file_data type: {type(file_data)}")

            resp = await self.client.put(url, content=content, headers=headers)
            resp.raise_for_status()
            return url

        except httpx.ReadTimeout:
            logger.exception(f"Timeout while uploading {object_name}")
            raise
        except httpx.HTTPStatusError as exc:
            logger.exception(f"Failed to upload {object_name}: {exc.response.status_code}")
            raise

    async def delete_file(self, object_name: str):
        url = f"{self.endpoint_url}/{self.bucket}/{object_name}"
        resp = await self.client.delete(url)
        resp.raise_for_status()

    async def copy_file(self, source_object: str, dest_object: str, public: bool = True):
        url = f"{self.endpoint_url}/{self.bucket}/{dest_object}"
        headers = {
            "x-amz-copy-source": f"/{self.bucket}/{quote(source_object)}",
        }
        if public:
            headers["x-amz-acl"] = "public-read"

        resp = await self.client.put(url, headers=headers)
        resp.raise_for_status()

    def get_url(self, object_name: str) -> str:
        bucket_host = self.endpoint_url.split("://", 1)[1].split("/", 1)[0]
        return f"https://{self.bucket}.{bucket_host}/{object_name}"
