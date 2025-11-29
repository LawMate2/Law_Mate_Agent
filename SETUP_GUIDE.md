# Google Services MCP Server 설정 가이드

## 1. Google Cloud 프로젝트 설정

### 1.1 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 상단 프로젝트 선택 드롭다운 클릭
3. "새 프로젝트" 클릭
4. 프로젝트 이름 입력 (예: "MCP Google Services")
5. "만들기" 클릭

### 1.2 API 활성화

1. 좌측 메뉴에서 "API 및 서비스" > "라이브러리" 선택
2. 다음 API들을 검색하여 활성화:
   - **Gmail API**
   - **Google Drive API**
   - **Google Calendar API**

각 API를 클릭하고 "사용 설정" 버튼을 클릭합니다.

### 1.3 OAuth 동의 화면 구성

1. "API 및 서비스" > "OAuth 동의 화면" 선택
2. 사용자 유형 선택:
   - **외부**: 모든 Google 계정 사용 가능
   - **내부**: Google Workspace 조직 내부만 (조직이 있는 경우)
3. "만들기" 클릭
4. 앱 정보 입력:
   - 앱 이름: `Google Services MCP`
   - 사용자 지원 이메일: 본인 이메일
   - 개발자 연락처: 본인 이메일
5. "저장 후 계속" 클릭

### 1.4 범위(Scopes) 추가

1. "범위 추가 또는 삭제" 클릭
2. 다음 범위 검색 및 추가:
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.compose`
   - `https://www.googleapis.com/auth/drive.file`
   - `https://www.googleapis.com/auth/drive`
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/calendar.events`
3. "업데이트" 클릭
4. "저장 후 계속" 클릭

### 1.5 테스트 사용자 추가 (개발 단계)

1. "테스트 사용자" 섹션에서 "사용자 추가" 클릭
2. 본인 Gmail 주소 입력
3. "추가" 클릭
4. "저장 후 계속" 클릭

### 1.6 OAuth 2.0 클라이언트 ID 생성

1. "API 및 서비스" > "사용자 인증 정보" 선택
2. 상단 "+ 사용자 인증 정보 만들기" 클릭
3. "OAuth 클라이언트 ID" 선택
4. 애플리케이션 유형: **데스크톱 앱** 선택
5. 이름 입력 (예: "MCP Desktop Client")
6. "만들기" 클릭
7. **credentials.json 다운로드**

## 2. 프로젝트 설정

### 2.1 의존성 설치

```bash
# 가상환경 생성 (권장)
python -m venv venv

# 가상환경 활성화
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2.2 인증 파일 배치

1. 다운로드한 `credentials.json` 파일을 `config/` 폴더에 복사:

```bash
mkdir -p config
cp ~/Downloads/credentials.json config/
```

2. 파일 구조 확인:
```
java_2nd_project_mcp/
├── config/
│   └── credentials.json  ← 여기에 배치
```

### 2.3 환경 변수 설정

1. `.env.example`을 `.env`로 복사:

```bash
cp .env.example .env
```

2. `.env` 파일 편집 (선택사항):
   - 대부분의 설정은 `credentials.json`에서 자동으로 읽어옵니다
   - 필요한 경우 포트 등을 변경할 수 있습니다

## 3. 첫 실행 및 인증

### 3.1 초기 인증

```bash
# MCP 서버 실행
python -m src.mcp_server
```

### 3.2 OAuth 인증 플로우

1. 브라우저가 자동으로 열립니다
2. Google 계정 선택
3. 권한 요청 화면에서:
   - "이 앱은 확인되지 않았습니다" 경고가 나타날 수 있습니다
   - "고급" 클릭 → "Google Services MCP(으)로 이동" 클릭
4. 요청된 권한 검토 및 "계속" 클릭
5. "Authentication successful!" 메시지 확인
6. `config/token.json` 파일이 자동 생성됨

### 3.3 인증 확인

```bash
# Python 인터프리터에서 확인
python
>>> from src.auth import GoogleAuthManager
>>> auth = GoogleAuthManager()
>>> creds = auth.get_credentials()
>>> print("인증 성공!" if creds else "인증 실패")
```

## 4. 테스트

### 4.1 예제 코드 실행

```bash
python example_usage.py
```

메뉴에서 원하는 예제 선택:
1. Gmail 서비스 테스트
2. Drive 서비스 테스트
3. Calendar 서비스 테스트
4. 통합 워크플로우 테스트

### 4.2 개별 서비스 테스트

```python
from datetime import datetime, timedelta
from src.auth import GoogleAuthManager
from src.google_services.gmail_service import GmailService, EmailMessage

# 인증
auth = GoogleAuthManager()
creds = auth.get_credentials()

# Gmail 테스트
gmail = GmailService(creds)
email = EmailMessage(
    to="test@example.com",
    subject="테스트",
    body="테스트 메시지"
)
result = gmail.send_email(email)
print(result)
```

## 5. MCP 서버 통합

### 5.1 Claude Desktop 설정

Claude Desktop의 `claude_desktop_config.json`에 추가:

```json
{
  "mcpServers": {
    "google-services": {
      "command": "python",
      "args": ["-m", "src.mcp_server"],
      "cwd": "/path/to/java_2nd_project_mcp",
      "env": {
        "PYTHONPATH": "/path/to/java_2nd_project_mcp"
      }
    }
  }
}
```

### 5.2 서버 실행 확인

Claude Desktop을 재시작하고 다음과 같이 테스트:

```
사용자: Google Calendar에 내일 오후 2시에 회의 일정을 추가해줘
Claude: [create_calendar_event 도구 사용]
```

## 6. 문제 해결

### 6.1 "credentials.json not found" 오류

- `config/credentials.json` 파일이 올바른 위치에 있는지 확인
- 파일 권한 확인: `chmod 600 config/credentials.json`

### 6.2 "insufficient permission" 오류

- OAuth 동의 화면에서 필요한 범위(Scopes)가 모두 추가되었는지 확인
- `config/token.json` 삭제 후 재인증

### 6.3 브라우저가 열리지 않음

- 수동으로 표시된 URL을 브라우저에 복사하여 붙여넣기
- 또는 `src/auth.py`의 `run_local_server` 부분 수정

### 6.4 "This app isn't verified" 경고

- 개발 단계에서는 정상적인 현상
- "고급" → "앱 이름으로 이동" 클릭하여 계속 진행
- 프로덕션 배포 시에는 Google의 앱 검증 프로세스 진행 필요

## 7. 보안 권장사항

1. **인증 파일 보호**
   ```bash
   chmod 600 config/credentials.json
   chmod 600 config/token.json
   ```

2. **Git에서 제외**
   - `.gitignore`에 다음 추가됨:
     ```
     config/credentials.json
     config/token.json
     .env
     ```

3. **정기적인 토큰 갱신**
   - 토큰은 자동으로 갱신되지만, 문제 발생 시 수동 갱신:
   ```bash
   rm config/token.json
   python -m src.mcp_server
   ```

## 8. 다음 단계

설정이 완료되었다면:

1. [README.md](README.md)에서 사용법 확인
2. [example_usage.py](example_usage.py)로 각 기능 테스트
3. 자신의 MCP 클라이언트에 통합
4. 필요에 따라 도메인 모델 확장

## 참고 자료

- [Google Cloud Console](https://console.cloud.google.com/)
- [Gmail API 문서](https://developers.google.com/gmail/api)
- [Drive API 문서](https://developers.google.com/drive/api)
- [Calendar API 문서](https://developers.google.com/calendar/api)
- [MCP 프로토콜](https://modelcontextprotocol.io/)