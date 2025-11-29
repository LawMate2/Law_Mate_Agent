"""
Gmail 서비스 도메인
이메일 발송 기능 제공
"""
from typing import Optional, List, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import base64
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class EmailMessage:
    """이메일 메시지 도메인 모델"""

    def __init__(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: bool = False,
        attachments: Optional[List[str]] = None
    ):
        self.to = to
        self.subject = subject
        self.body = body
        self.cc = cc or []
        self.bcc = bcc or []
        self.html = html
        self.attachments = attachments or []

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "to": self.to,
            "subject": self.subject,
            "body": self.body,
            "cc": self.cc,
            "bcc": self.bcc,
            "html": self.html,
            "attachments": self.attachments
        }


class GmailService:
    """Gmail 서비스"""

    def __init__(self, credentials):
        """
        Gmail 서비스 초기화

        Args:
            credentials: Google OAuth 인증 정보
        """
        self.credentials = credentials
        self.service = build('gmail', 'v1', credentials=credentials)

    def create_message(self, email: EmailMessage) -> Dict[str, Any]:
        """
        이메일 메시지 생성

        Args:
            email: EmailMessage 객체

        Returns:
            Gmail API 형식의 메시지
        """
        if email.html:
            message = MIMEMultipart('alternative')
        else:
            message = MIMEMultipart()

        message['to'] = email.to
        message['subject'] = email.subject

        if email.cc:
            message['cc'] = ', '.join(email.cc)
        if email.bcc:
            message['bcc'] = ', '.join(email.bcc)

        # 본문 추가
        if email.html:
            part = MIMEText(email.body, 'html')
        else:
            part = MIMEText(email.body, 'plain')
        message.attach(part)

        # 첨부파일 추가
        for filepath in email.attachments:
            self._attach_file(message, filepath)

        # Base64 인코딩
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return {'raw': raw_message}

    def _attach_file(self, message: MIMEMultipart, filepath: str):
        """파일 첨부"""
        with open(filepath, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            filename = filepath.split('/')[-1]
            part.add_header('Content-Disposition', f'attachment; filename={filename}')
            message.attach(part)

    def send_email(self, email: EmailMessage) -> Dict[str, Any]:
        """
        이메일 발송

        Args:
            email: EmailMessage 객체

        Returns:
            발송 결과 (메시지 ID 포함)

        Raises:
            HttpError: Gmail API 오류
        """
        try:
            message = self.create_message(email)
            sent_message = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()

            return {
                "success": True,
                "message_id": sent_message['id'],
                "thread_id": sent_message.get('threadId'),
                "to": email.to,
                "subject": email.subject
            }

        except HttpError as error:
            return {
                "success": False,
                "error": str(error),
                "error_code": error.resp.status
            }

    def send_bulk_emails(self, emails: List[EmailMessage]) -> List[Dict[str, Any]]:
        """
        대량 이메일 발송

        Args:
            emails: EmailMessage 리스트

        Returns:
            각 이메일의 발송 결과 리스트
        """
        results = []
        for email in emails:
            result = self.send_email(email)
            results.append(result)
        return results