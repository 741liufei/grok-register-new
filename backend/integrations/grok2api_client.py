# -*- coding: utf-8 -*-
"""Grok2API 管理端登录与账号凭据导入。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable

from curl_cffi import CurlMime, requests


class Grok2APIImportError(RuntimeError):
    """远程 Grok2API 登录或导入失败。"""


def normalize_base_url(value: str) -> str:
    base = str(value or "").strip().rstrip("/")
    if not base:
        raise Grok2APIImportError("Grok2API API 地址为空")
    if not base.startswith(("http://", "https://")):
        raise Grok2APIImportError("Grok2API API 地址必须以 http:// 或 https:// 开头")
    return base


def remote_configured(config: Dict[str, Any]) -> bool:
    return all(
        str(config.get(key, "") or "").strip()
        for key in (
            "grok2api_remote_url",
            "grok2api_remote_username",
            "grok2api_remote_password",
        )
    )


def _error_message(response: Any, fallback: str) -> str:
    try:
        payload = response.json()
    except Exception:
        payload = None
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict) and error.get("message"):
            return str(error["message"])
        if payload.get("message"):
            return str(payload["message"])
    status = int(getattr(response, "status_code", 0) or 0)
    return f"{fallback} (HTTP {status})" if status else fallback


def login(
    base_url: str,
    username: str,
    password: str,
    *,
    timeout: float = 20,
    session: Any = None,
) -> str:
    base = normalize_base_url(base_url)
    user = str(username or "").strip()
    secret = str(password or "")
    if not user or not secret:
        raise Grok2APIImportError("Grok2API 管理员账号或密码为空")
    client = session or requests.Session()
    try:
        response = client.post(
            f"{base}/api/admin/v1/auth/login",
            json={"username": user, "password": secret},
            headers={"Accept": "application/json"},
            timeout=timeout,
        )
    except Exception as exc:
        raise Grok2APIImportError(f"连接 Grok2API 登录接口失败: {exc}") from exc
    if int(getattr(response, "status_code", 0) or 0) != 200:
        raise Grok2APIImportError(_error_message(response, "Grok2API 登录失败"))
    try:
        payload = response.json()
        token = str(payload["data"]["tokens"]["accessToken"] or "").strip()
    except (KeyError, TypeError, ValueError) as exc:
        raise Grok2APIImportError("Grok2API 登录响应缺少 accessToken") from exc
    if not token:
        raise Grok2APIImportError("Grok2API 登录响应缺少 accessToken")
    return token


def _iter_sse_events(lines: Iterable[Any]) -> Iterable[tuple[str, Dict[str, Any]]]:
    event = "message"
    data_lines: list[str] = []
    for raw in lines:
        if isinstance(raw, bytes):
            line = raw.decode("utf-8", errors="replace")
        else:
            line = str(raw or "")
        line = line.rstrip("\r\n")
        if not line:
            if data_lines:
                raw_data = "\n".join(data_lines)
                try:
                    payload = json.loads(raw_data)
                except json.JSONDecodeError:
                    payload = {"message": raw_data}
                yield event, payload if isinstance(payload, dict) else {"data": payload}
            event, data_lines = "message", []
            continue
        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            event = line[6:].strip() or "message"
        elif line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
    if data_lines:
        raw_data = "\n".join(data_lines)
        try:
            payload = json.loads(raw_data)
        except json.JSONDecodeError:
            payload = {"message": raw_data}
        yield event, payload if isinstance(payload, dict) else {"data": payload}


def import_auth_file(
    base_url: str,
    access_token: str,
    file_path: str | Path,
    *,
    timeout: float = 120,
    session: Any = None,
) -> Dict[str, Any]:
    base = normalize_base_url(base_url)
    token = str(access_token or "").strip()
    if not token:
        raise Grok2APIImportError("Grok2API accessToken 为空")
    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        raise Grok2APIImportError("Grok2API 授权 JSON 文件不存在")
    try:
        content = path.read_bytes()
        json.loads(content.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Grok2APIImportError(f"Grok2API 授权 JSON 无效: {exc}") from exc
    client = session or requests.Session()
    multipart = CurlMime()
    multipart.addpart(
        name="files",
        filename=path.name,
        content_type="application/json",
        data=content,
    )
    try:
        request_kwargs = {
            "headers": {
                "Accept": "text/event-stream",
                "Authorization": f"Bearer {token}",
                "Cache-Control": "no-cache",
            },
            "multipart": multipart,
            "timeout": timeout,
            "stream": True,
        }
        try:
            response = client.post(
                f"{base}/api/admin/v1/accounts/import",
                **request_kwargs,
            )
        except TypeError as exc:
            # 测试替身或兼容客户端可能仅实现 requests 风格的 files 参数。
            if "multipart" not in str(exc):
                raise
            request_kwargs.pop("multipart", None)
            request_kwargs["files"] = {
                "files": (path.name, content, "application/json")
            }
            response = client.post(
                f"{base}/api/admin/v1/accounts/import",
                **request_kwargs,
            )
    except Exception as exc:
        multipart.close()
        raise Grok2APIImportError(f"连接 Grok2API 导入接口失败: {exc}") from exc
    if int(getattr(response, "status_code", 0) or 0) != 200:
        multipart.close()
        raise Grok2APIImportError(_error_message(response, "Grok2API 导入失败"))
    completed: Dict[str, Any] | None = None
    try:
        for event, payload in _iter_sse_events(response.iter_lines()):
            if event == "error":
                raise Grok2APIImportError(
                    str(
                        payload.get("message")
                        or payload.get("code")
                        or "Grok2API 导入失败"
                    )
                )
            if event == "complete":
                completed = payload
    finally:
        try:
            response.close()
        except Exception:
            pass
        multipart.close()
    if completed is None:
        raise Grok2APIImportError("Grok2API 导入响应未返回 complete 事件")
    return completed


def import_with_credentials(
    config: Dict[str, Any],
    file_path: str | Path,
    *,
    timeout: float = 120,
    session: Any = None,
) -> Dict[str, Any]:
    if not remote_configured(config):
        raise Grok2APIImportError("请先完整配置 Grok2API API 地址、管理员账号和密码")
    client = session or requests.Session()
    token = login(
        str(config.get("grok2api_remote_url") or ""),
        str(config.get("grok2api_remote_username") or ""),
        str(config.get("grok2api_remote_password") or ""),
        session=client,
    )
    return import_auth_file(
        str(config.get("grok2api_remote_url") or ""),
        token,
        file_path,
        timeout=timeout,
        session=client,
    )
