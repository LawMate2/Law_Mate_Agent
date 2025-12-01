FROM python:3.11-slim

WORKDIR /app

# 기본 파이썬 런타임 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 시스템 패키지 최소 설치
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY src ./src
COPY main.py example_usage.py README.md SETUP_GUIDE.md ./

# OAuth 토큰/자격증명을 저장할 디렉터리
RUN mkdir -p /app/config

# HTTP 서버 포트
EXPOSE 8000

# 기본 엔트리포인트
CMD ["python", "-m", "src.http_server"]
