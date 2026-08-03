# -*- coding: utf-8 -*-
"""账号重新登录后台任务。

Web 请求只负责启动任务；浏览器登录、SSO 刷新与授权文件重建在单独线程执行。
"""
from __future__ import annotations

import datetime
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional


class ReloginJobCoordinator:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._running = False
        self._account_id = 0
        self._email = ""
        self._stage = "等待启动"
        self._error = ""
        self._started_at: Optional[float] = None
        self._finished_at: Optional[float] = None
        self._thread: Optional[threading.Thread] = None

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "running": self._running,
                "account_id": self._account_id,
                "email": self._email,
                "stage": self._stage,
                "error": self._error,
                "started_at": self._started_at,
                "finished_at": self._finished_at,
            }

    def _set(self, **values: Any) -> None:
        with self._lock:
            for key, value in values.items():
                setattr(self, f"_{key}", value)

    def start(self, account_id: int) -> Dict[str, Any]:
        from backend.registration import engine as gr

        store = gr.get_registration_repository()
        records = store.get_results_by_ids([account_id])
        if not records:
            raise LookupError("记录不存在")
        record = records[0]
        email = str(record.get("email") or "").strip()
        password = str(record.get("password") or "")
        if not email or "@" not in email:
            raise ValueError("账号记录缺少有效邮箱")
        if not password:
            raise ValueError("账号记录没有保存密码")

        with self._lock:
            if self._running:
                raise RuntimeError(f"账号 {self._email or self._account_id} 正在重新登录")
            self._running = True
            self._account_id = int(account_id)
            self._email = email
            self._stage = "启动浏览器"
            self._error = ""
            self._started_at = time.time()
            self._finished_at = None

        def runner() -> None:
            from backend.automation.session import stop_browser
            from backend.registration.login_flow import capture_login_failure, login_with_password

            cpa_detail: Dict[str, Any] = {}
            account_file = ""
            screenshot_path = ""

            def log(message: str) -> None:
                text = str(message or "")
                if "打开重新登录页" in text:
                    self._set(stage="填写邮箱和密码")
                elif "等待 sso" in text:
                    self._set(stage="等待新的 SSO")
                elif "[CPA]" in text:
                    self._set(stage="重建授权文件")

            try:
                gr.load_config()
                gr._wire_runtime_modules()
                gr._bs.allow_browser_launches()
                sso = login_with_password(email, password, timeout=100, log_callback=log)

                self._set(stage="保存账号文件")
                account_path = Path(gr.account_file_for_email(email))
                account_path.parent.mkdir(parents=True, exist_ok=True)
                temporary = account_path.with_name(f".{account_path.name}.{uuid.uuid4().hex}.tmp")
                temporary.write_text(f"{email}----{password}----{sso}\n", encoding="utf-8")
                try:
                    os.chmod(temporary, 0o600)
                except OSError:
                    pass
                os.replace(temporary, account_path)
                account_file = str(account_path)

                self._set(stage="重建 CPA / Grok2API 文件")
                cpa_ok = gr.add_sso_to_cpa(
                    sso,
                    email=email,
                    log_callback=log,
                    result_out=cpa_detail,
                )
                cpa_success = cpa_ok and str(cpa_detail.get("status") or "") == "success"
                relogin_status = "success" if cpa_success else "partial"
                error = "" if cpa_success else str(cpa_detail.get("error") or "授权文件重建未完成")
                store.update_relogin_result(
                    account_id,
                    account_file=account_file,
                    cpa_detail=cpa_detail,
                    status=relogin_status,
                    error=error,
                )
                if not cpa_success:
                    raise RuntimeError(error)
                self._set(stage="重新登录完成", error="")
            except Exception as exc:
                error = str(exc)
                stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                safe_email = email.replace("/", "_").replace("\\", "_")
                screenshot_path = capture_login_failure(
                    Path(gr.DATA_DIR)
                    / "screenshots"
                    / "relogin-failures"
                    / f"relogin-{account_id}-{safe_email}-{stamp}.png"
                )
                store.update_relogin_result(
                    account_id,
                    account_file=account_file,
                    cpa_detail=cpa_detail,
                    status="partial" if account_file else "failed",
                    error=error,
                    screenshot_path=screenshot_path,
                )
                self._set(stage="重新登录失败", error=error)
            finally:
                try:
                    stop_browser(force=True)
                except BaseException:
                    pass
                self._set(running=False, finished_at=time.time())

        self._thread = threading.Thread(
            target=runner,
            name=f"account-relogin-{account_id}",
            daemon=True,
        )
        self._thread.start()
        return self.status()


relogin_coordinator = ReloginJobCoordinator()
