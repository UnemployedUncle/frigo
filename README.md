# 요리 여정

요리 여정은 냉장고에 있는 재료를 자연어로 정리하고, 그 재료를 바탕으로 레시피를 추천하고, 장보기 목록과 단계별 workflow까지 이어지는 MVP를 만드는 프로젝트입니다.

현재 문서는 장기 비전보다 `지금 구현하고 테스트할 수 있는 MVP` 기준으로 정리되어 있습니다.

## 현재 MVP 범위

이번 MVP에서 실제로 구현하는 기능은 아래 4가지입니다.

- 냉장고 자연어 입력 및 재료 표 관리
- 레시피 검색 plan 기반 추천
- 장보기 목록 생성
- 레시피 workflow 조회 및 단계 이동

이번 MVP에서 제외하는 기능은 아래와 같습니다.

- 홈 대시보드
- 주간 식단 추천
- 주간 장보기 최적화
- 개인화 추천 고도화
- 운영 로그 및 호출 로그

## 환경 변수 설정

이 프로젝트는 OpenRouter를 사용할 수 있도록 환경 변수 파일을 기준으로 API 키를 관리합니다.

1. 루트 디렉터리에서 `.env.example`을 참고해 `.env` 파일을 준비합니다.
2. `.env` 파일의 `OPENROUTER_API_KEY`에 본인의 OpenRouter API 키를 입력합니다.
3. `OPENROUTER_BASE_URL`은 기본값 `https://openrouter.ai/api/v1`을 사용합니다.
4. `DATABASE_URL`은 PostgreSQL 연결 문자열을 사용합니다.

예시:

```bash
cp .env.example .env
```

`.env` 파일 예시:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
DATABASE_URL=postgresql://frigo:frigo@localhost:5432/frigo
```

보안을 위해 `.env`는 `.gitignore`에 포함되어 있으며, 실제 API 키는 저장소에 커밋하지 않습니다.

## Agent 모델 구성

현재 프로젝트의 모든 agent는 OpenRouter를 통해 동일한 모델을 사용합니다.

- 냉장고 관리 agent: `nvidia/nemotron-3-super-120b-a12b:free`
- 레시피 검색 plan agent: `nvidia/nemotron-3-super-120b-a12b:free`
- 장보기 목록 agent: `nvidia/nemotron-3-super-120b-a12b:free`
- workflow 구성 agent: `nvidia/nemotron-3-super-120b-a12b:free`

현재는 모든 agent가 `:free` 모델로 고정되어 같은 LLM을 바라봅니다. 이후 기능별로 다른 모델을 연결할 수 있도록 확장 가능한 구조를 전제로 합니다.

OpenRouter 예시 호출 코드는 [openrouter_ex.py](/Users/yongsupyi/Desktop/frigo/Archive/openrouter_ex.py)에 정리되어 있습니다.

## 로컬 실행

Docker가 준비되어 있다면 아래 방식으로 앱과 PostgreSQL을 함께 실행합니다.

```bash
docker compose up --build
```

앱 컨테이너는 시작 시 migration, recipe seed 적재, workflow 검증을 먼저 수행한 뒤 FastAPI 서버를 실행합니다.

## 현재 MVP 흐름

1. 사용자가 냉장고 재료를 자연어로 입력합니다.
2. 냉장고 관리 agent가 입력을 구조화해 PostgreSQL에 저장합니다.
3. 저장된 재료는 표 형태로 조회, 수정, 삭제할 수 있습니다.
4. 레시피 검색 agent가 냉장고 재료로 검색 plan을 만들고 레시피를 추천합니다.
5. 장보기 목록 agent가 없는 재료와 절반 이하 재고를 계산합니다.
6. 선택한 레시피의 workflow jsonl을 읽어 단계별 화면으로 보여줍니다.

## 핵심 데이터

- 레시피 seed 데이터: [recipes.jsonl](/Users/yongsupyi/Desktop/frigo/data/recipes.jsonl)
- workflow 데이터: [data/workflows](/Users/yongsupyi/Desktop/frigo/data/workflows)
- 상세 개발 기준: [prd.md](/Users/yongsupyi/Desktop/frigo/prd.md)

## GitHub 업로드용 경량 구성

이 저장소는 GitHub 업로드 시 코드 중심으로만 올리고, 대용량 raw 데이터와 seed 데이터는 로컬에만 두는 구성을 지원합니다.

- `Raw/full_dataset.csv`는 로컬 전용입니다.
- `data/recipes.jsonl`, `data/workflows/*.jsonl`, `data/staging/*`도 로컬 전용입니다.
- GitHub에는 코드, 설정 파일, 문서, 로컬 데이터 안내 파일만 올립니다.

로컬에서 다시 실행하려면 아래 경로를 직접 준비해야 합니다.

- `Raw/full_dataset.csv`
- `data/recipes.jsonl`
- `data/workflows/*.jsonl`

세부 경로 규칙은 [data/README.md](/Users/yongsupyi/Desktop/frigo/data/README.md)에 정리되어 있습니다.

## 향후 확장

- 기능별 모델 다변화
- 주간 식단 추천
- 주간 장보기 최적화
- 추천 랭킹 고도화
- 사용자 개인화
