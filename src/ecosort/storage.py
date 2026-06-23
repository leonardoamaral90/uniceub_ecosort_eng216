from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Iterable

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from ecosort.config import Settings, get_settings


def s3_client(settings: Settings | None = None):
    settings = settings or get_settings()
    return boto3.client(
        "s3",
        endpoint_url=f"http://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def ensure_buckets(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    client = s3_client(settings)
    for bucket in [settings.minio_bucket_bronze, settings.minio_bucket_silver, settings.minio_bucket_gold]:
        try:
            client.head_bucket(Bucket=bucket)
        except ClientError:
            client.create_bucket(Bucket=bucket)


def upload_file(bucket: str, key: str, file_path: Path, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    client = s3_client(settings)
    content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    client.upload_file(str(file_path), bucket, key, ExtraArgs={"ContentType": content_type})


def upload_directory(bucket: str, prefix: str, local_dir: Path, settings: Settings | None = None) -> int:
    settings = settings or get_settings()
    count = 0
    for file_path in local_dir.rglob("*"):
        if file_path.is_file():
            key = f"{prefix.rstrip('/')}/{file_path.relative_to(local_dir).as_posix()}"
            upload_file(bucket, key, file_path, settings)
            count += 1
    return count


def list_local_files(paths: Iterable[Path], suffixes: set[str] | None = None) -> list[Path]:
    files: list[Path] = []
    suffixes = {s.lower() for s in suffixes} if suffixes else None
    for path in paths:
        if not path.exists():
            continue
        for file_path in path.rglob("*"):
            if file_path.is_file() and (suffixes is None or file_path.suffix.lower() in suffixes):
                files.append(file_path)
    return sorted(files)
