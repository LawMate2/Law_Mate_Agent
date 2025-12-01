# Google Services MCP Server

Google Gmail, Drive, Calendar를 통합한 MCP (Model Context Protocol) 서버입니다.

## 기능

### 1. Gmail 서비스
- 이메일 발송
- HTML 이메일 지원
- 참조(CC), 숨은참조(BCC) 지원
- 첨부파일 지원

### 2. Google Drive 서비스
- 파일 업로드
- 계약서 전용 폴더 관리
- 파일 공유
- 메타데이터 관리

### 3. Google Calendar 서비스
- 일정 생성
- 회의 일정 생성
- 계약 마감일 등록
- 알림 설정

## 설치

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. Google Cloud 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. API 활성화:
   - Gmail API
   - Google Drive API
   - Google Calendar API
4. OAuth 2.0 클라이언트 ID 생성:
   - 사용자 인증 정보 > OAuth 2.0 클라이언트 ID 생성
   - 애플리케이션 유형: 데스크톱 앱
   - credentials.json 다운로드
5. `config/credentials.json` 경로에 파일 배치

### 3. 환경 변수 설정

`.env.example`을 `.env`로 복사하고 필요한 값을 설정합니다:

```bash
cp .env .env
```

```env
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

## 사용법

### MCP 서버 실행

```bash
python -m src.mcp_server
```

### HTTP 서버 (포트 8000)로 요청 받기

1. 환경 변수/토큰 준비  
   - `config/credentials.json` 배치 후 한 번 `python -m src.mcp_server`를 실행하거나, 토큰이 없다면 최초 요청 시 브라우저 인증이 열립니다.  
   - 생성된 `config/token.json`은 재사용되므로 이후에는 로그인 단계 없이 동작합니다.
2. 서버 실행  
   ```bash
   python -m src.http_server
   # 또는
   python src/http_server.py
   ```
3. 요청 보내기 (`POST /tasks`)  
   ```bash
   curl -X POST http://localhost:8000/tasks \
     -H "Content-Type: application/json" \
     -d '{
       "request_id": "req-123",
       "type": "email",
       "timezone": "Asia/Seoul",
       "payload": {
         "to": "user@example.com",
         "subject": "테스트 메일",
         "body": "본문",
         "cc": [],
         "bcc": [],
         "html": false,
         "attachments": []
       }
     }'
   ```
   - `type`에 따라 필요한 필드가 다릅니다.  
     - `email`: `to`, `subject`, `body` 필수, 선택 `cc`, `bcc`, `html`, `attachments`(로컬 경로 배열)  
     - `calendar`: `summary`, `start_time`, `end_time`(ISO 8601) 필수, 선택 `description`, `location`, `attendees`, `reminders`(분 단위), `all_day`, `timezone`  
     - `drive`: `file_path`, `contract_name` 필수, 선택 `contract_date`, `parties`, `folder_name`
   - 응답 예시  
     ```json
     {
       "success": true,
       "request_id": "req-123",
       "type": "calendar",
       "result": {
         "success": true,
         "event_id": "...",
         "summary": "회의",
         "start": { "dateTime": "2024-12-01T14:00:00+09:00" },
         "end": { "dateTime": "2024-12-01T15:00:00+09:00" },
         "html_link": "https://..."
       }
     }
     ```

### 도구 사용 예제

#### 1. 이메일 발송

```json
{
  "tool": "send_email",
  "arguments": {
    "to": "recipient@example.com",
    "subject": "안녕하세요",
    "body": "이메일 본문 내용",
    "cc": ["cc@example.com"],
    "html": false
  }
}
```

#### 2. 계약서 업로드

```json
{
  "tool": "upload_contract",
  "arguments": {
    "file_path": "/path/to/contract.pdf",
    "contract_name": "2024년 서비스 계약서",
    "contract_date": "2024-01-15",
    "parties": ["회사A", "회사B"],
    "folder_name": "Contracts"
  }
}
```

#### 3. 일정 생성

```json
{
  "tool": "create_calendar_event",
  "arguments": {
    "summary": "프로젝트 회의",
    "start_time": "2024-12-01T14:00:00",
    "end_time": "2024-12-01T15:00:00",
    "description": "프로젝트 진행 상황 논의",
    "location": "회의실 A",
    "attendees": ["member1@example.com", "member2@example.com"],
    "all_day": false
  }
}
```

#### 4. 계약 마감일 등록

```json
{
  "tool": "create_contract_deadline",
  "arguments": {
    "contract_name": "2024년 서비스 계약",
    "deadline_date": "2024-12-31T23:59:59",
    "description": "계약 갱신 검토 필요",
    "reminder_days": [1, 3, 7]
  }
}
```

## 프로젝트 구조

```
java_2nd_project_mcp/
├── src/
│   ├── google_services/
│   │   ├── __init__.py
│   │   ├── gmail_service.py      # Gmail 서비스 도메인
│   │   ├── drive_service.py      # Drive 서비스 도메인
│   │   └── calendar_service.py   # Calendar 서비스 도메인
│   ├── __init__.py
│   ├── auth.py                   # OAuth 인증 관리
│   ├── config.py                 # 설정 관리
│   └── mcp_server.py            # MCP 서버 메인
├── config/
│   ├── credentials.json         # Google OAuth 인증 정보 (직접 배치)
│   └── token.json              # 자동 생성되는 액세스 토큰
├── requirements.txt
├── .env.example
└── README.md
```

## 도메인 모델

### EmailMessage
- 이메일 발송을 위한 도메인 모델
- 받는 사람, 제목, 본문, 참조, HTML 지원

### DriveFile
- 드라이브 파일 업로드를 위한 도메인 모델
- 파일 경로, MIME 타입, 폴더 ID, 메타데이터

### CalendarEvent
- 캘린더 이벤트를 위한 도메인 모델
- 제목, 시작/종료 시간, 참석자, 알림 설정

## LLM 에이전트 통합

이 MCP 서버는 다음과 같은 도구를 LLM 에이전트에 제공합니다:

1. `send_email`: 이메일 발송
2. `upload_contract`: 계약서 드라이브 업로드
3. `create_calendar_event`: 일정 생성
4. `create_contract_deadline`: 계약 마감일 등록

LLM은 이 도구들을 사용하여 자연어 명령을 실행 가능한 작업으로 변환합니다.

## 보안

- OAuth 2.0 인증 사용
- 토큰은 로컬에 안전하게 저장
- `.env` 파일과 `credentials.json`은 반드시 `.gitignore`에 추가

## 라이선스

MIT
