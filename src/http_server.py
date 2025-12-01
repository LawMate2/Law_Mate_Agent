"""HTTP 서버 (포트 8001)로 Gmail/Calendar/Drive 작업을 받는 엔드포인트."""
import asyncio
from datetime import datetime
import base64
import tempfile
import os
from pathlib import Path
from typing import Any, Dict, Literal, Optional
from uuid import uuid4

from aiohttp import web
from pydantic import BaseModel, Field, ValidationError

from src.auth import GoogleAuthManager


# CORS 설정
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
from src.google_services.calendar_service import CalendarEvent, CalendarService
from src.google_services.drive_service import DriveService
from src.google_services.gmail_service import EmailMessage, GmailService


class TaskRequest(BaseModel):
    """포트 8000에서 받는 공통 요청 모델."""

    request_id: str = Field(default_factory=lambda: uuid4().hex)
    type: Literal["email", "calendar", "drive"]
    timezone: str = Field(default="Asia/Seoul", description="캘린더용 타임존")
    payload: Dict[str, Any]


class GoogleTaskRouter:
    """Google 서비스 호출을 라우팅하는 헬퍼."""

    def __init__(self):
        self.auth_manager = GoogleAuthManager()
        self.credentials = None
        self.gmail_service: Optional[GmailService] = None
        self.drive_service: Optional[DriveService] = None
        self.calendar_service: Optional[CalendarService] = None

    def _ensure_services(self):
        if self.credentials:
            return

        self.credentials = self.auth_manager.get_credentials()
        self.gmail_service = GmailService(self.credentials)
        self.drive_service = DriveService(self.credentials)
        self.calendar_service = CalendarService(self.credentials)

    async def dispatch(self, task: TaskRequest) -> Dict[str, Any]:
        """type에 따라 각 서비스로 분기."""
        self._ensure_services()

        if task.type == "email":
            return await self._handle_email(task.payload)
        if task.type == "calendar":
            return await self._handle_calendar(task.payload, task.timezone)
        if task.type == "drive":
            return await self._handle_drive(task.payload)

        raise ValueError(f"Unsupported task type: {task.type}")

    async def _handle_email(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        required = ["to", "subject", "body"]
        _validate_required(payload, required, "email")

        email = EmailMessage(
            to=payload["to"],
            subject=payload["subject"],
            body=payload["body"],
            cc=payload.get("cc", []),
            bcc=payload.get("bcc", []),
            html=payload.get("html", False),
            attachments=payload.get("attachments", []),
        )

        return await asyncio.to_thread(self.gmail_service.send_email, email)

    async def _handle_calendar(self, payload: Dict[str, Any], timezone: str) -> Dict[str, Any]:
        required = ["summary", "start_time", "end_time"]
        _validate_required(payload, required, "calendar")

        event = CalendarEvent(
            summary=payload["summary"],
            start_time=datetime.fromisoformat(payload["start_time"]),
            end_time=datetime.fromisoformat(payload["end_time"]),
            description=payload.get("description"),
            location=payload.get("location"),
            attendees=payload.get("attendees", []),
            reminders=payload.get("reminders"),
            timezone=timezone,
            all_day=payload.get("all_day", False),
        )

        return await asyncio.to_thread(self.calendar_service.create_event, event)

    async def _handle_drive(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        required = ["contract_name"]
        _validate_required(payload, required, "drive")

        temp_file_path = None
        try:
            # 파일 경로 또는 base64 컨텐츠 둘 중 하나를 지원
            file_path = payload.get("file_path")
            file_content_b64 = payload.get("file_content_b64")
            file_name = payload.get("file_name") or payload["contract_name"]

            if file_content_b64:
                suffix = Path(file_name).suffix or ".bin"
                fd, temp_file_path = tempfile.mkstemp(suffix=suffix, prefix="mcp_drive_")
                with os.fdopen(fd, "wb") as temp_file:
                    temp_file.write(base64.b64decode(file_content_b64))
                file_path = temp_file_path

            if not file_path:
                raise web.HTTPBadRequest(
                    text="drive payload missing fields: file_path or file_content_b64",
                    content_type="application/json",
                )

            metadata = {}
            if payload.get("contract_date"):
                metadata["contract_date"] = payload["contract_date"]
            if payload.get("parties"):
                metadata["parties"] = ",".join(payload["parties"])

            return await asyncio.to_thread(
                self.drive_service.upload_contract,
                contract_file_path=file_path,
                contract_name=payload["contract_name"],
                contract_metadata=metadata,
                folder_name=payload.get("folder_name", "Contracts"),
            )
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except OSError:
                    pass


def _validate_required(payload: Dict[str, Any], fields: list[str], section: str):
    missing = [field for field in fields if field not in payload]
    if missing:
        raise web.HTTPBadRequest(
            text=f"{section} payload missing fields: {', '.join(missing)}",
            content_type="application/json",
        )


@web.middleware
async def cors_middleware(request: web.Request, handler):
    """CORS 헤더를 추가하는 미들웨어."""
    # OPTIONS 요청 처리 (preflight)
    if request.method == "OPTIONS":
        origin = request.headers.get("Origin", "")
        if origin in ALLOWED_ORIGINS:
            return web.Response(
                status=200,
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                    "Access-Control-Max-Age": "3600",
                },
            )
        return web.Response(status=403)

    # 실제 요청 처리
    response = await handler(request)
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

    return response


async def handle_task(request: web.Request) -> web.Response:
    """POST /tasks 엔드포인트."""
    try:
        body = await request.json()
    except Exception:
        raise web.HTTPBadRequest(text='Invalid JSON body', content_type="application/json")

    try:
        task = TaskRequest(**body)
    except ValidationError as exc:
        return web.json_response(
            {"success": False, "error": "validation_error", "details": exc.errors()},
            status=400,
        )

    router: GoogleTaskRouter = request.app["router"]

    try:
        result = await router.dispatch(task)
        return web.json_response(
            {
                "success": True,
                "request_id": task.request_id,
                "type": task.type,
                "result": result,
            }
        )
    except web.HTTPException:
        raise
    except Exception as exc:
        return web.json_response(
            {
                "success": False,
                "request_id": task.request_id,
                "type": task.type,
                "error": str(exc),
            },
            status=500,
        )


def create_app() -> web.Application:
    """AIOHTTP 애플리케이션 생성."""
    app = web.Application(middlewares=[cors_middleware])
    app["router"] = GoogleTaskRouter()
    app.router.add_post("/tasks", handle_task)
    app.router.add_get("/health", lambda _: web.json_response({"status": "ok"}))
    return app


def main():
    app = create_app()
    port = int(os.getenv("MCP_HTTP_PORT", "8001"))
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
