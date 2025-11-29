"""
Google Services MCP Server 사용 예제
각 도메인 서비스를 테스트하는 예제 코드
"""
from datetime import datetime, timedelta
from src.auth import GoogleAuthManager
from src.google_services.gmail_service import GmailService, EmailMessage
from src.google_services.drive_service import DriveService, DriveFile
from src.google_services.calendar_service import CalendarService, CalendarEvent


def example_gmail():
    """Gmail 서비스 사용 예제"""
    print("\n=== Gmail 서비스 예제 ===")

    # 인증
    auth_manager = GoogleAuthManager()
    credentials = auth_manager.get_credentials()
    gmail_service = GmailService(credentials)

    # 이메일 발송
    email = EmailMessage(
        to="recipient@example.com",
        subject="테스트 이메일",
        body="이것은 MCP 서버를 통한 테스트 이메일입니다.",
        cc=["cc@example.com"],
        html=False
    )

    result = gmail_service.send_email(email)
    print(f"이메일 발송 결과: {result}")


def example_drive():
    """Drive 서비스 사용 예제"""
    print("\n=== Drive 서비스 예제 ===")

    # 인증
    auth_manager = GoogleAuthManager()
    credentials = auth_manager.get_credentials()
    drive_service = DriveService(credentials)

    # 계약서 업로드
    result = drive_service.upload_contract(
        contract_file_path="/path/to/contract.pdf",
        contract_name="2024년 서비스 계약서",
        contract_metadata={
            "contract_date": "2024-01-15",
            "parties": "회사A,회사B",
            "type": "서비스 계약"
        },
        folder_name="Contracts"
    )

    print(f"계약서 업로드 결과: {result}")

    # 파일 공유 (업로드 성공 시)
    if result.get("success") and result.get("file_id"):
        share_result = drive_service.share_file(
            file_id=result["file_id"],
            email="partner@example.com",
            role="reader",
            send_notification=True
        )
        print(f"파일 공유 결과: {share_result}")


def example_calendar():
    """Calendar 서비스 사용 예제"""
    print("\n=== Calendar 서비스 예제 ===")

    # 인증
    auth_manager = GoogleAuthManager()
    credentials = auth_manager.get_credentials()
    calendar_service = CalendarService(credentials)

    # 1. 일반 일정 생성
    tomorrow = datetime.now() + timedelta(days=1)
    event = CalendarEvent(
        summary="프로젝트 회의",
        start_time=tomorrow.replace(hour=14, minute=0, second=0),
        end_time=tomorrow.replace(hour=15, minute=0, second=0),
        description="프로젝트 진행 상황 논의",
        location="회의실 A",
        attendees=["member1@example.com", "member2@example.com"],
        reminders=[10, 30]
    )

    result = calendar_service.create_event(event)
    print(f"일정 생성 결과: {result}")

    # 2. 계약 마감일 등록
    deadline = datetime.now() + timedelta(days=30)
    deadline_result = calendar_service.create_contract_deadline(
        contract_name="2024년 서비스 계약",
        deadline_date=deadline,
        description="계약 갱신 검토 필요",
        reminder_days=[1, 3, 7]
    )

    print(f"계약 마감일 등록 결과: {deadline_result}")

    # 3. 다가오는 일정 조회
    upcoming = calendar_service.get_upcoming_events(max_results=5)
    print(f"\n다가오는 일정 ({upcoming.get('count')}개):")
    for event in upcoming.get('events', []):
        print(f"  - {event['summary']} ({event['start']})")


def example_integrated_workflow():
    """통합 워크플로우 예제: 계약서 처리 전체 프로세스"""
    print("\n=== 통합 워크플로우 예제 ===")
    print("계약서 업로드 → 이메일 발송 → 마감일 등록")

    # 인증
    auth_manager = GoogleAuthManager()
    credentials = auth_manager.get_credentials()

    gmail_service = GmailService(credentials)
    drive_service = DriveService(credentials)
    calendar_service = CalendarService(credentials)

    # 1. 계약서 드라이브 업로드
    print("\n1. 계약서 업로드 중...")
    upload_result = drive_service.upload_contract(
        contract_file_path="/path/to/contract.pdf",
        contract_name="2024년 파트너십 계약서",
        contract_metadata={
            "contract_date": datetime.now().strftime("%Y-%m-%d"),
            "parties": "우리회사,파트너회사"
        }
    )

    if not upload_result.get("success"):
        print(f"업로드 실패: {upload_result}")
        return

    print(f"✓ 업로드 완료: {upload_result.get('web_view_link')}")

    # 2. 파트너에게 이메일 발송
    print("\n2. 파트너에게 이메일 발송 중...")
    email = EmailMessage(
        to="partner@example.com",
        subject="[계약서] 2024년 파트너십 계약서",
        body=f"""
안녕하세요,

2024년 파트너십 계약서를 첨부하여 보내드립니다.

계약서 링크: {upload_result.get('web_view_link')}

검토 부탁드립니다.

감사합니다.
        """.strip(),
        cc=["legal@ourcompany.com"]
    )

    email_result = gmail_service.send_email(email)
    print(f"✓ 이메일 발송 완료: {email_result.get('message_id')}")

    # 3. 계약 마감일 캘린더 등록
    print("\n3. 계약 마감일 등록 중...")
    deadline = datetime.now() + timedelta(days=365)
    calendar_result = calendar_service.create_contract_deadline(
        contract_name="2024년 파트너십 계약서",
        deadline_date=deadline,
        description="계약 갱신 검토 및 파트너와 협의 필요",
        reminder_days=[1, 7, 30]
    )

    print(f"✓ 마감일 등록 완료: {calendar_result.get('html_link')}")

    print("\n=== 모든 작업 완료 ===")


if __name__ == "__main__":
    print("Google Services MCP Server 사용 예제")
    print("=====================================")

    # 실행할 예제 선택
    choice = input("""
예제를 선택하세요:
1. Gmail 서비스
2. Drive 서비스
3. Calendar 서비스
4. 통합 워크플로우 (계약서 처리 전체 프로세스)
선택 (1-4): """)

    if choice == "1":
        example_gmail()
    elif choice == "2":
        example_drive()
    elif choice == "3":
        example_calendar()
    elif choice == "4":
        example_integrated_workflow()
    else:
        print("잘못된 선택입니다.")