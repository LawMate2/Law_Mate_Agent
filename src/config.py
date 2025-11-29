"""
설정 관리 모듈
환경 변수 및 Google OAuth 설정
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """애플리케이션 설정"""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/oauth/callback")

    # Service Account (선택사항)
    GOOGLE_SERVICE_ACCOUNT_FILE: Optional[str] = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")

    # Server
    PORT: int = int(os.getenv("PORT", "8080"))
    HOST: str = os.getenv("HOST", "localhost")

    # OAuth Scopes
    GMAIL_SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.compose'
    ]

    DRIVE_SCOPES = [
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive'
    ]

    CALENDAR_SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ]

    # All Scopes Combined
    ALL_SCOPES = GMAIL_SCOPES + DRIVE_SCOPES + CALENDAR_SCOPES

    # Token Storage
    TOKEN_FILE = Path(__file__).parent.parent / "config" / "token.json"
    CREDENTIALS_FILE = Path(__file__).parent.parent / "config" / "credentials.json"

    @classmethod
    def validate(cls) -> bool:
        """설정 유효성 검사"""
        if not cls.GOOGLE_CLIENT_ID or not cls.GOOGLE_CLIENT_SECRET:
            return False
        return True