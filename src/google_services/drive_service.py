"""
Google Drive 서비스 도메인
파일 업로드 및 관리 기능 제공 (계약서 저장)
"""
from typing import Optional, Dict, Any, List
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


class DriveFile:
    """드라이브 파일 도메인 모델"""

    def __init__(
        self,
        name: str,
        filepath: str,
        mime_type: Optional[str] = None,
        folder_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.filepath = filepath
        self.mime_type = mime_type or self._detect_mime_type()
        self.folder_id = folder_id
        self.description = description
        self.metadata = metadata or {}

    def _detect_mime_type(self) -> str:
        """파일 확장자로 MIME 타입 감지"""
        extension_map = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.zip': 'application/zip'
        }
        ext = Path(self.filepath).suffix.lower()
        return extension_map.get(ext, 'application/octet-stream')

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "name": self.name,
            "filepath": self.filepath,
            "mime_type": self.mime_type,
            "folder_id": self.folder_id,
            "description": self.description,
            "metadata": self.metadata
        }


class DriveService:
    """Google Drive 서비스"""

    def __init__(self, credentials):
        """
        Drive 서비스 초기화

        Args:
            credentials: Google OAuth 인증 정보
        """
        self.credentials = credentials
        self.service = build('drive', 'v3', credentials=credentials)

    def create_folder(
        self,
        folder_name: str,
        parent_folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        폴더 생성

        Args:
            folder_name: 폴더 이름
            parent_folder_id: 상위 폴더 ID (없으면 루트)

        Returns:
            생성된 폴더 정보
        """
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }

            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]

            folder = self.service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink'
            ).execute()

            return {
                "success": True,
                "folder_id": folder['id'],
                "folder_name": folder['name'],
                "web_link": folder.get('webViewLink')
            }

        except HttpError as error:
            return {
                "success": False,
                "error": str(error),
                "error_code": error.resp.status
            }

    def upload_file(self, drive_file: DriveFile) -> Dict[str, Any]:
        """
        파일 업로드

        Args:
            drive_file: DriveFile 객체

        Returns:
            업로드 결과 (파일 ID, 링크 포함)
        """
        try:
            file_metadata = {
                'name': drive_file.name
            }

            if drive_file.folder_id:
                file_metadata['parents'] = [drive_file.folder_id]

            if drive_file.description:
                file_metadata['description'] = drive_file.description

            # 커스텀 메타데이터 추가
            if drive_file.metadata:
                file_metadata['properties'] = drive_file.metadata

            media = MediaFileUpload(
                drive_file.filepath,
                mimetype=drive_file.mime_type,
                resumable=True
            )

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, webContentLink, mimeType, size, createdTime'
            ).execute()

            return {
                "success": True,
                "file_id": file['id'],
                "file_name": file['name'],
                "web_view_link": file.get('webViewLink'),
                "download_link": file.get('webContentLink'),
                "mime_type": file.get('mimeType'),
                "size": file.get('size'),
                "created_time": file.get('createdTime')
            }

        except HttpError as error:
            return {
                "success": False,
                "error": str(error),
                "error_code": error.resp.status
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"File not found: {drive_file.filepath}"
            }

    def upload_contract(
        self,
        contract_file_path: str,
        contract_name: str,
        contract_metadata: Optional[Dict[str, Any]] = None,
        folder_name: str = "Contracts"
    ) -> Dict[str, Any]:
        """
        계약서 업로드 (전용 폴더에 저장)

        Args:
            contract_file_path: 계약서 파일 경로
            contract_name: 계약서 이름
            contract_metadata: 계약서 메타데이터 (계약 날짜, 당사자 등)
            folder_name: 저장할 폴더 이름 (기본: Contracts)

        Returns:
            업로드 결과
        """
        # 계약서 폴더 찾기 또는 생성
        folder_result = self._find_or_create_folder(folder_name)

        if not folder_result['success']:
            return folder_result

        folder_id = folder_result['folder_id']

        # 계약서 파일 업로드
        drive_file = DriveFile(
            name=contract_name,
            filepath=contract_file_path,
            folder_id=folder_id,
            description="Contract Document",
            metadata=contract_metadata
        )

        return self.upload_file(drive_file)

    def _find_or_create_folder(self, folder_name: str) -> Dict[str, Any]:
        """폴더 찾기 또는 생성"""
        try:
            # 폴더 검색
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            folders = results.get('files', [])

            if folders:
                # 기존 폴더 사용
                return {
                    "success": True,
                    "folder_id": folders[0]['id'],
                    "folder_name": folders[0]['name'],
                    "created": False
                }
            else:
                # 새 폴더 생성
                result = self.create_folder(folder_name)
                if result['success']:
                    result['created'] = True
                return result

        except HttpError as error:
            return {
                "success": False,
                "error": str(error),
                "error_code": error.resp.status
            }

    def share_file(
        self,
        file_id: str,
        email: str,
        role: str = 'reader',
        send_notification: bool = True
    ) -> Dict[str, Any]:
        """
        파일 공유

        Args:
            file_id: 공유할 파일 ID
            email: 공유할 사용자 이메일
            role: 권한 (reader, writer, commenter)
            send_notification: 이메일 알림 전송 여부

        Returns:
            공유 결과
        """
        try:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }

            self.service.permissions().create(
                fileId=file_id,
                body=permission,
                sendNotificationEmail=send_notification
            ).execute()

            return {
                "success": True,
                "file_id": file_id,
                "shared_with": email,
                "role": role
            }

        except HttpError as error:
            return {
                "success": False,
                "error": str(error),
                "error_code": error.resp.status
            }