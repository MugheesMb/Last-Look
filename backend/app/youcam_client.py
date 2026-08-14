
import asyncio
import io
import json
import mimetypes
import zipfile
from pathlib import Path
from typing import Any

import httpx

from app.config import settings

POLL_INTERVAL_SECONDS = 2
POLL_TIMEOUT_SECONDS = 120


class YouCamAPIError(RuntimeError):
    pass


class YouCamClient:
    def __init__(self) -> None:
        self._base = settings.youcam_api_base
        self._headers = {
            "Authorization": f"Bearer {settings.youcam_api_key}",
            "Content-Type": "application/json",
        }

    async def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self._base, headers=self._headers, timeout=30)

    async def upload_file(self, task_type: str, file_path: str) -> str:
        """Uploads a local image file for the given task type. Returns file_id."""
        path = Path(file_path)
        content_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        with open(path, "rb") as f:
            file_bytes = f.read()
        return await self.upload_bytes(task_type, path.name, content_type, file_bytes)

    async def upload_bytes(self, task_type: str, file_name: str, content_type: str, file_bytes: bytes) -> str:
        """Uploads raw image bytes (no file needed on disk) for the given task type. Returns file_id."""
        file_size = len(file_bytes)

        async with await self._client() as client:
            resp = await client.post(
                f"/s2s/v2.0/file/{task_type}",
                json={
                    "files": [
                        {
                            "content_type": content_type,
                            "file_name": file_name,
                            "file_size": file_size,
                        }
                    ]
                },
            )
            resp.raise_for_status()
            body = resp.json()
            data = body["result"] if "result" in body else body["data"]
            file_info = data["files"][0]
            file_id = file_info["file_id"]

            request_info = file_info.get("requests", [{}])[0] if "requests" in file_info else file_info
            upload_url = request_info.get("url") or file_info.get("url")
            if not upload_url:
                raise YouCamAPIError(
                    f"Couldn't find an upload URL in the file-upload response. "
                    f"Raw file_info for debugging: {file_info}"
                )

            upload_headers = self._parse_upload_headers(request_info.get("headers"))

            # Use a bare client with none of the YouCam auth/content-type
            # defaults for the actual upload — presigned S3 URLs carry their
            # own signature in the query string, and S3 rejects requests that
            # also send an Authorization header ("multiple auth mechanisms")
            # or an unexpected Content-Type not covered by the signature.
            async with httpx.AsyncClient(timeout=30) as upload_client:
                put_resp = await upload_client.put(
                    upload_url,
                    content=file_bytes,
                    headers=upload_headers or {"Content-Type": content_type},
                )
                if put_resp.status_code >= 400:
                    raise YouCamAPIError(
                        f"S3 upload failed ({put_resp.status_code}). "
                        f"Response body: {put_resp.text[:1000]}"
                    )

        return file_id

    @staticmethod
    def _parse_upload_headers(raw_headers) -> dict[str, str]:
        """Handles the several shapes an upload-headers field could realistically
        take, since we don't have a live response to confirm the exact one:
        - a plain dict already ({"Content-Type": "image/jpeg"})
        - a list of {"key": ..., "value": ...} or {"name": ..., "value": ...} objects
        - a list of "Header-Name: value" strings
        - missing/None entirely
        """
        if not raw_headers:
            return {}

        if isinstance(raw_headers, dict):
            return {str(k): str(v) for k, v in raw_headers.items()}

        parsed: dict[str, str] = {}
        if isinstance(raw_headers, list):
            for item in raw_headers:
                if isinstance(item, dict):
                    key = item.get("key") or item.get("name")
                    value = item.get("value")
                    if key is not None and value is not None:
                        parsed[str(key)] = str(value)
                elif isinstance(item, str) and ":" in item:
                    key, _, value = item.partition(":")
                    parsed[key.strip()] = value.strip()
        return parsed

    async def start_task(self, task_type: str, payload: dict[str, Any]) -> str:
        """POSTs a task and returns task_id."""
        async with await self._client() as client:
            resp = await client.post(f"/s2s/v2.0/task/{task_type}", json=payload)
            if resp.status_code >= 400:
                raise YouCamAPIError(
                    f"Task creation failed for {task_type} ({resp.status_code}). "
                    f"Payload sent: {payload}. Response body: {resp.text[:1000]}"
                )
            body = resp.json()
            data = body.get("data") or body.get("result") or body
            task_id = data["task_id"]
        return task_id

    async def poll_task(self, task_type: str, task_id: str) -> dict[str, Any]:
        """Polls until success/error or timeout. Returns final result payload."""
        elapsed = 0
        async with await self._client() as client:
            while elapsed < POLL_TIMEOUT_SECONDS:
                resp = await client.get(f"/s2s/v2.0/task/{task_type}/{task_id}")
                if resp.status_code >= 400:
                    raise YouCamAPIError(
                        f"Task poll failed for {task_type}/{task_id} ({resp.status_code}). "
                        f"Response body: {resp.text[:1000]}"
                    )
                body = resp.json()
                data = body.get("data") or body.get("result") or body
                status = data.get("task_status") or data.get("status")

                if status == "success":
                    return data
                if status == "error":
                    raise YouCamAPIError(f"YouCam task {task_type}/{task_id} failed: {data}")

                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                elapsed += POLL_INTERVAL_SECONDS

        raise YouCamAPIError(f"YouCam task {task_type}/{task_id} timed out after {POLL_TIMEOUT_SECONDS}s")

    # SD (standard-definition) skin concern set for the skin-analysis task's
    # required dst_actions field. HD concerns use the same names with an
    # hd_ prefix, but SD and HD cannot be mixed in a single request — we
    # stick to SD here since it's the lighter-weight option for a demo.
    SD_SKIN_CONCERNS = [
        "wrinkle",
        "droopy_upper_eyelid",
        "droopy_lower_eyelid",
        "firmness",
        "acne",
        "moisture",
        "eye_bag",
        "dark_circle_v2",
        "age_spot",
        "radiance",
        "redness",
        "oiliness",
        "pore",
        "texture",
    ]

    async def run_skin_analysis(self, *, src_file_url: str | None = None, src_file_id: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"dst_actions": self.SD_SKIN_CONCERNS}
        if src_file_id:
            payload["src_file_id"] = src_file_id
        elif src_file_url:
            payload["src_file_url"] = src_file_url
        else:
            raise ValueError("Provide src_file_url or src_file_id")

        task_id = await self.start_task("skin-analysis", payload)
        task_result = await self.poll_task("skin-analysis", task_id)

        # Skin Analysis doesn't return scores inline — "results" is a
        # presigned URL to a ZIP containing the actual JSON data (confirmed
        # from a real response; earlier code wrongly assumed inline JSON).
        zip_url = (task_result.get("results") or {}).get("url")
        if not zip_url:
            return task_result  # unexpected shape — let the caller's debug logging catch it

        return await self._download_and_extract_result_json(zip_url)

    async def _download_and_extract_result_json(self, zip_url: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(zip_url)
            resp.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            json_names = [n for n in zf.namelist() if n.lower().endswith(".json")]
            if not json_names:
                raise YouCamAPIError(
                    f"No JSON file found in the Skin Analysis result ZIP. "
                    f"Files present: {zf.namelist()}"
                )
            with zf.open(json_names[0]) as f:
                return json.load(f)

    async def run_cloth_tryon(
        self,
        *,
        src_file_url: str | None = None,
        src_file_id: str | None = None,
        ref_file_url: str | None = None,
        ref_file_id: str | None = None,
        garment_category: str = "auto",
    ) -> dict[str, Any]:
        # "auto" lets YouCam detect the garment type from the reference image
        # itself, rather than guessing an exact enum string (e.g. "top" was
        # rejected as invalid — the real accepted values aren't published,
        # but "auto" is confirmed in Perfect Corp's own changelog).
        payload: dict[str, Any] = {
            "garment_category": garment_category,
            "change_shoes": False,  # required alongside garment_category; we're not touching footwear
        }
        if src_file_id:
            payload["src_file_id"] = src_file_id
        elif src_file_url:
            payload["src_file_url"] = src_file_url
        else:
            raise ValueError("Provide src_file_url or src_file_id")

        if ref_file_id:
            payload["ref_file_id"] = ref_file_id
        elif ref_file_url:
            payload["ref_file_url"] = ref_file_url
        else:
            raise ValueError("Provide ref_file_url or ref_file_id")

        task_id = await self.start_task("cloth", payload)
        return await self.poll_task("cloth", task_id)


youcam_client = YouCamClient()
