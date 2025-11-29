"""
Google OAuth 인증 관리
"""
import os
import json
from pathlib import Path
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from src.config import Config


class GoogleAuthManager:
    """Google OAuth 인증 관리자"""

    def __init__(self):
        self.token_file = Config.TOKEN_FILE
        self.credentials_file = Config.CREDENTIALS_FILE
        self.scopes = Config.ALL_SCOPES
        self.credentials: Optional[Credentials] = None

    def get_credentials(self) -> Credentials:
        """
        OAuth 인증 정보 가져오기
        토큰이 없거나 만료된 경우 새로 인증

        Returns:
            Credentials: Google OAuth 인증 정보
        """
        # 기존 토큰 로드
        if self.token_file.exists():
            self.credentials = Credentials.from_authorized_user_file(
                str(self.token_file),
                self.scopes
            )

        # 토큰이 없거나 유효하지 않은 경우
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                # 토큰 갱신
                print("Refreshing access token...")
                self.credentials.refresh(Request())
            else:
                # 새로운 인증 플로우
                print("Starting new OAuth flow...")
                self.credentials = self._authenticate_new()

            # 토큰 저장
            self._save_token()

        return self.credentials

    def _authenticate_new(self) -> Credentials:
        """새로운 OAuth 인증 플로우"""
        if not self.credentials_file.exists():
            raise FileNotFoundError(
                f"Credentials file not found: {self.credentials_file}\n"
                "Please download it from Google Cloud Console and place it in the config directory."
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(self.credentials_file),
            self.scopes
        )

        # 로컬 서버로 인증
        credentials = flow.run_local_server(
            port=Config.PORT,
            success_message='Authentication successful! You can close this window.',
            open_browser=True
        )

        return credentials

    def _save_token(self):
        """토큰 저장"""
        # 디렉토리 생성
        self.token_file.parent.mkdir(parents=True, exist_ok=True)

        # 토큰 저장
        with open(self.token_file, 'w') as token:
            token.write(self.credentials.to_json())

        print(f"Token saved to {self.token_file}")

    def revoke_credentials(self):
        """인증 취소"""
        if self.credentials:
            self.credentials.revoke(Request())

        # 토큰 파일 삭제
        if self.token_file.exists():
            self.token_file.unlink()

        print("Credentials revoked and token file deleted")

    def is_authenticated(self) -> bool:
        """인증 상태 확인"""
        if not self.token_file.exists():
            return False

        try:
            credentials = Credentials.from_authorized_user_file(
                str(self.token_file),
                self.scopes
            )
            return credentials.valid
        except Exception:
            return False