"""
MCP Server for Google Services Integration
Gmail, Drive, Calendar 통합 서버
"""
import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field

from src.auth import GoogleAuthManager
from src.google_services.gmail_service import GmailService, EmailMessage
from src.google_services.drive_service import DriveService, DriveFile
from src.google_services.calendar_service import CalendarService, CalendarEvent


# Pydantic 모델 정의
class SendEmailRequest(BaseModel):
    """이메일 발송 요청"""
    to: str = Field(description="받는 사람 이메일")
    subject: str = Field(description="이메일 제목")
    body: str = Field(description="이메일 본문")
    cc: List[str] = Field(default=[], description="참조 이메일 리스트")
    bcc: List[str] = Field(default=[], description="숨은 참조 이메일 리스트")
    html: bool = Field(default=False, description="HTML 형식 사용 여부")


class UploadContractRequest(BaseModel):
    """계약서 업로드 요청"""
    file_path: str = Field(description="계약서 파일 경로")
    contract_name: str = Field(description="계약서 이름")
    contract_date: str = Field(default=None, description="계약 날짜 (YYYY-MM-DD)")
    parties: List[str] = Field(default=[], description="계약 당사자")
    folder_name: str = Field(default="Contracts", description="저장할 폴더명")


class CreateEventRequest(BaseModel):
    """일정 생성 요청"""
    summary: str = Field(description="일정 제목")
    start_time: str = Field(description="시작 시간 (ISO 8601)")
    end_time: str = Field(description="종료 시간 (ISO 8601)")
    description: str = Field(default=None, description="일정 설명")
    location: str = Field(default=None, description="장소")
    attendees: List[str] = Field(default=[], description="참석자 이메일 리스트")
    all_day: bool = Field(default=False, description="종일 일정 여부")


class GoogleServicesMCPServer:
    """Google Services MCP Server"""

    def __init__(self):
        self.server = Server("google-services-mcp")
        self.auth_manager = GoogleAuthManager()
        self.credentials = None
        self.gmail_service = None
        self.drive_service = None
        self.calendar_service = None

        # 도구 등록
        self._register_tools()

    def _initialize_services(self):
        """서비스 초기화"""
        if not self.credentials:
            self.credentials = self.auth_manager.get_credentials()
            self.gmail_service = GmailService(self.credentials)
            self.drive_service = DriveService(self.credentials)
            self.calendar_service = CalendarService(self.credentials)

    def _register_tools(self):
        """MCP 도구 등록"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """사용 가능한 도구 목록"""
            return [
                Tool(
                    name="send_email",
                    description="Gmail을 사용하여 이메일을 발송합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "to": {
                                "type": "string",
                                "description": "받는 사람 이메일 주소"
                            },
                            "subject": {
                                "type": "string",
                                "description": "이메일 제목"
                            },
                            "body": {
                                "type": "string",
                                "description": "이메일 본문"
                            },
                            "cc": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "참조(CC) 이메일 리스트"
                            },
                            "bcc": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "숨은참조(BCC) 이메일 리스트"
                            },
                            "html": {
                                "type": "boolean",
                                "description": "HTML 형식 사용 여부"
                            }
                        },
                        "required": ["to", "subject", "body"]
                    }
                ),
                Tool(
                    name="upload_contract",
                    description="계약서를 Google Drive에 업로드합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "업로드할 계약서 파일 경로"
                            },
                            "contract_name": {
                                "type": "string",
                                "description": "계약서 이름"
                            },
                            "contract_date": {
                                "type": "string",
                                "description": "계약 날짜 (YYYY-MM-DD 형식)"
                            },
                            "parties": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "계약 당사자 목록"
                            },
                            "folder_name": {
                                "type": "string",
                                "description": "저장할 폴더명 (기본: Contracts)"
                            }
                        },
                        "required": ["file_path", "contract_name"]
                    }
                ),
                Tool(
                    name="create_calendar_event",
                    description="Google Calendar에 일정을 생성합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "일정 제목"
                            },
                            "start_time": {
                                "type": "string",
                                "description": "시작 시간 (ISO 8601 형식)"
                            },
                            "end_time": {
                                "type": "string",
                                "description": "종료 시간 (ISO 8601 형식)"
                            },
                            "description": {
                                "type": "string",
                                "description": "일정 설명"
                            },
                            "location": {
                                "type": "string",
                                "description": "장소"
                            },
                            "attendees": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "참석자 이메일 리스트"
                            },
                            "all_day": {
                                "type": "boolean",
                                "description": "종일 일정 여부"
                            }
                        },
                        "required": ["summary", "start_time", "end_time"]
                    }
                ),
                Tool(
                    name="create_contract_deadline",
                    description="계약 마감일을 캘린더에 등록합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "contract_name": {
                                "type": "string",
                                "description": "계약명"
                            },
                            "deadline_date": {
                                "type": "string",
                                "description": "마감일 (ISO 8601 형식)"
                            },
                            "description": {
                                "type": "string",
                                "description": "계약 설명"
                            },
                            "reminder_days": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "알림 설정 (일 단위, 예: [1, 3, 7])"
                            }
                        },
                        "required": ["contract_name", "deadline_date"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> List[TextContent]:
            """도구 실행"""
            self._initialize_services()

            try:
                if name == "send_email":
                    return await self._handle_send_email(arguments)
                elif name == "upload_contract":
                    return await self._handle_upload_contract(arguments)
                elif name == "create_calendar_event":
                    return await self._handle_create_event(arguments)
                elif name == "create_contract_deadline":
                    return await self._handle_create_deadline(arguments)
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )]

    async def _handle_send_email(self, args: Dict[str, Any]) -> List[TextContent]:
        """이메일 발송 처리"""
        email = EmailMessage(
            to=args["to"],
            subject=args["subject"],
            body=args["body"],
            cc=args.get("cc", []),
            bcc=args.get("bcc", []),
            html=args.get("html", False)
        )

        result = self.gmail_service.send_email(email)

        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]

    async def _handle_upload_contract(self, args: Dict[str, Any]) -> List[TextContent]:
        """계약서 업로드 처리"""
        metadata = {}
        if args.get("contract_date"):
            metadata["contract_date"] = args["contract_date"]
        if args.get("parties"):
            metadata["parties"] = ",".join(args["parties"])

        result = self.drive_service.upload_contract(
            contract_file_path=args["file_path"],
            contract_name=args["contract_name"],
            contract_metadata=metadata,
            folder_name=args.get("folder_name", "Contracts")
        )

        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]

    async def _handle_create_event(self, args: Dict[str, Any]) -> List[TextContent]:
        """일정 생성 처리"""
        event = CalendarEvent(
            summary=args["summary"],
            start_time=datetime.fromisoformat(args["start_time"]),
            end_time=datetime.fromisoformat(args["end_time"]),
            description=args.get("description"),
            location=args.get("location"),
            attendees=args.get("attendees", []),
            all_day=args.get("all_day", False)
        )

        result = self.calendar_service.create_event(event)

        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]

    async def _handle_create_deadline(self, args: Dict[str, Any]) -> List[TextContent]:
        """계약 마감일 생성 처리"""
        result = self.calendar_service.create_contract_deadline(
            contract_name=args["contract_name"],
            deadline_date=datetime.fromisoformat(args["deadline_date"]),
            description=args.get("description"),
            reminder_days=args.get("reminder_days")
        )

        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]

    async def run(self):
        """서버 실행"""
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """메인 함수"""
    server = GoogleServicesMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
