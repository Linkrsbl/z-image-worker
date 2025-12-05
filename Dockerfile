FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 시스템 라이브러리 (이미지 저장/로드용)
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1) CUDA 12.1 버전의 PyTorch 설치 (GPU 사용)
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu121 \
    torch torchvision torchaudio

# 2) 나머지 파이썬 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) 핸들러 코드 복사
COPY . .

# RunPod 서버리스 진입점
CMD ["python", "-u", "rp_handler.py"]
