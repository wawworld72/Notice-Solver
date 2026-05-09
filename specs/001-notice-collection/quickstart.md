# Quickstart: Notice-Solver

## 사전 준비

```bash
# Python 3.11+ 확인
python --version

# uv 설치 (없을 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# LibreOffice 설치 (HWP 변환용, 선택)
sudo apt-get install libreoffice   # Ubuntu/Debian
brew install --cask libreoffice    # macOS
```

## 설치

```bash
git clone https://github.com/wawworld72/Notice-Solver.git
cd Notice-Solver
uv sync
```

## 설정

```bash
cp .env.example .env
# .env 편집: GITHUB_TOKEN, GITHUB_REPO_OWNER, GITHUB_REPO_NAME
```

## 기본 사용 (4단계)

```bash
# Phase 1: 공지 수집 (증분, 기본)
uv run notice-solver collect --board MAPP_1708240139

# Phase 2: 자산 Issue 생성
uv run notice-solver assets create

# Phase 2.5: OCR 처리 (배치, 50건씩)
uv run notice-solver ocr run --limit 50

# 현황 확인
uv run notice-solver status
```

## 전체 수집 (최초 1회)

```bash
# 전체 재수집 (~3,600건, 약 60분 소요)
uv run notice-solver collect --full

# 자산 일괄 생성
uv run notice-solver assets create --limit 1000

# OCR 야간 배치 실행
uv run notice-solver ocr run --limit 200 --type image
uv run notice-solver ocr run --limit 100 --type attachment
```

## 테스트

```bash
uv run pytest tests/ -v
uv run pytest tests/unit/ -v          # 단위 테스트만
uv run pytest tests/integration/ -v  # 통합 테스트만
```
