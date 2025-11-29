"""
Google Calendar 서비스 도메인
일정 생성 및 관리 기능 제공
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class CalendarEvent:
    """캘린더 이벤트 도메인 모델"""

    def __init__(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        reminders: Optional[List[int]] = None,
        timezone: str = 'Asia/Seoul',
        all_day: bool = False
    ):
        self.summary = summary
        self.start_time = start_time
        self.end_time = end_time
        self.description = description
        self.location = location
        self.attendees = attendees or []
        self.reminders = reminders or [30]  # 기본 30분 전 알림
        self.timezone = timezone
        self.all_day = all_day

    def to_google_event(self) -> Dict[str, Any]:
        """Google Calendar API 형식으로 변환"""
        event = {
            'summary': self.summary,
            'description': self.description,
            'location': self.location,
        }

        # 시작/종료 시간 설정
        if self.all_day:
            event['start'] = {
                'date': self.start_time.strftime('%Y-%m-%d'),
                'timeZone': self.timezone,
            }
            event['end'] = {
                'date': self.end_time.strftime('%Y-%m-%d'),
                'timeZone': self.timezone,
            }
        else:
            event['start'] = {
                'dateTime': self.start_time.isoformat(),
                'timeZone': self.timezone,
            }
            event['end'] = {
                'dateTime': self.end_time.isoformat(),
                'timeZone': self.timezone,
            }

        # 참석자 추가
        if self.attendees:
            event['attendees'] = [{'email': email} for email in self.attendees]

        # 알림 설정
        if self.reminders:
            event['reminders'] = {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': minutes}
                    for minutes in self.reminders
                ]
            }

        return event

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "summary": self.summary,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "description": self.description,
            "location": self.location,
            "attendees": self.attendees,
            "reminders": self.reminders,
            "timezone": self.timezone,
            "all_day": self.all_day
        }


class CalendarService:
    """Google Calendar 서비스"""

    def __init__(self, credentials):
        """
        Calendar 서비스 초기화

        Args:
            credentials: Google OAuth 인증 정보
        """
        self.credentials = credentials
        self.service = build('calendar', 'v3', credentials=credentials)

    def create_event(
        self,
        event: CalendarEvent,
        calendar_id: str = 'primary',
        send_notifications: bool = True
    ) -> Dict[str, Any]:
        """
        일정 생성

        Args:
            event: CalendarEvent 객체
            calendar_id: 캘린더 ID (기본: primary)
            send_notifications: 참석자에게 알림 전송 여부

        Returns:
            생성된 일정 정보
        """
        try:
            google_event = event.to_google_event()

            created_event = self.service.events().insert(
                calendarId=calendar_id,
                body=google_event,
                sendNotifications=send_notifications
            ).execute()

            return {
                "success": True,
                "event_id": created_event['id'],
                "summary": created_event['summary'],
                "start": created_event['start'],
                "end": created_event['end'],
                "html_link": created_event.get('htmlLink'),
                "hangout_link": created_event.get('hangoutLink')
            }

        except HttpError as error:
            return {
                "success": False,
                "error": str(error),
                "error_code": error.resp.status
            }

    def create_meeting_event(
        self,
        title: str,
        start_time: datetime,
        duration_minutes: int,
        attendees: List[str],
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        회의 일정 생성 (간편 메서드)

        Args:
            title: 회의 제목
            start_time: 시작 시간
            duration_minutes: 회의 시간 (분)
            attendees: 참석자 이메일 리스트
            description: 회의 설명
            location: 회의 장소

        Returns:
            생성된 일정 정보
        """
        end_time = start_time + timedelta(minutes=duration_minutes)

        event = CalendarEvent(
            summary=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            attendees=attendees,
            reminders=[10, 30]  # 10분, 30분 전 알림
        )

        return self.create_event(event)

    def create_contract_deadline(
        self,
        contract_name: str,
        deadline_date: datetime,
        description: Optional[str] = None,
        reminder_days: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        계약 마감일 일정 생성

        Args:
            contract_name: 계약명
            deadline_date: 마감일
            description: 설명
            reminder_days: 알림 일수 (예: [1, 3, 7] = 1일전, 3일전, 7일전)

        Returns:
            생성된 일정 정보
        """
        if reminder_days is None:
            reminder_days = [1, 3, 7]  # 기본: 1, 3, 7일 전

        # 분 단위로 변환 (일 * 24시간 * 60분)
        reminders_in_minutes = [days * 24 * 60 for days in reminder_days]

        event = CalendarEvent(
            summary=f"[계약 마감] {contract_name}",
            start_time=deadline_date,
            end_time=deadline_date + timedelta(hours=1),
            description=description or f"{contract_name} 계약 마감일",
            reminders=reminders_in_minutes,
            all_day=True
        )

        return self.create_event(event)

    def get_upcoming_events(
        self,
        max_results: int = 10,
        calendar_id: str = 'primary'
    ) -> Dict[str, Any]:
        """
        다가오는 일정 조회

        Args:
            max_results: 최대 결과 수
            calendar_id: 캘린더 ID

        Returns:
            일정 리스트
        """
        try:
            now = datetime.utcnow().isoformat() + 'Z'

            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            return {
                "success": True,
                "count": len(events),
                "events": [
                    {
                        "id": event['id'],
                        "summary": event['summary'],
                        "start": event['start'],
                        "end": event['end'],
                        "html_link": event.get('htmlLink')
                    }
                    for event in events
                ]
            }

        except HttpError as error:
            return {
                "success": False,
                "error": str(error),
                "error_code": error.resp.status
            }

    def update_event(
        self,
        event_id: str,
        updated_event: CalendarEvent,
        calendar_id: str = 'primary'
    ) -> Dict[str, Any]:
        """
        일정 수정

        Args:
            event_id: 수정할 일정 ID
            updated_event: 수정된 CalendarEvent 객체
            calendar_id: 캘린더 ID

        Returns:
            수정 결과
        """
        try:
            google_event = updated_event.to_google_event()

            updated = self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=google_event
            ).execute()

            return {
                "success": True,
                "event_id": updated['id'],
                "summary": updated['summary'],
                "updated": updated.get('updated')
            }

        except HttpError as error:
            return {
                "success": False,
                "error": str(error),
                "error_code": error.resp.status
            }

    def delete_event(
        self,
        event_id: str,
        calendar_id: str = 'primary'
    ) -> Dict[str, Any]:
        """
        일정 삭제

        Args:
            event_id: 삭제할 일정 ID
            calendar_id: 캘린더 ID

        Returns:
            삭제 결과
        """
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            return {
                "success": True,
                "event_id": event_id,
                "message": "Event deleted successfully"
            }

        except HttpError as error:
            return {
                "success": False,
                "error": str(error),
                "error_code": error.resp.status
            }
