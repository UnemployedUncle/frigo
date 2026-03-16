# 요리 여정 핵심 MVP PRD

## 1. 목표

이 문서는 요리 여정의 첫 MVP를 실제로 개발하기 위해 제품, agent, 데이터 저장 형식, 기술 스택을 확정한 PRD입니다. 이번 MVP는 아래 4개 흐름만 우선 구현합니다.

- 냉장고 자연어 입력 및 재료 관리
- 레시피 검색 계획 기반 추천
- 장보기 목록 생성
- 레시피 workflow 전환

## 2. 고정 기술 결정

- 모든 agent는 OpenRouter를 통해 동일한 LLM을 사용합니다.
- 기본 모델은 `nvidia/nemotron-3-super-120b-a12b:free`입니다.
- 추후 기능별로 모델을 다변화할 수 있도록 agent별 모델 설정 분리 구조를 전제로 설계합니다.
- 현재 단계에서는 냉장고 관리 agent, 레시피 검색 agent, 장보기 목록 agent, workflow 구성 agent가 모두 같은 모델을 바라봅니다.
- LLM 응답 형식은 자유 텍스트가 아니라 `JSON Schema 강제` 방식으로 받습니다.
- agent orchestration은 `LangChain`과 `LangGraph`로 구성합니다.
- 영속 저장소는 `PostgreSQL`로 고정합니다.
- rate limit, timeout, 호출 실패, 운영 로그, 호출 로그는 이번 MVP 구현 범위에서 제외하고 백로그로 남깁니다.

## 3. Agent 구성

### 3.1 냉장고 관리 Agent

- 역할: 자연어 입력을 고정 스키마의 재료 데이터로 변환
- 모델: `nvidia/nemotron-3-super-120b-a12b:free`
- 입력: 사용자 원문
- 출력: JSON Schema를 만족하는 재료 배열
- 저장 대상: PostgreSQL `fridge_items`, `fridge_input_logs`

### 3.2 레시피 검색 Plan Agent

- 역할: 냉장고 재료에서 검색용 주재료를 뽑고 단계별 검색 plan 생성
- 모델: `nvidia/nemotron-3-super-120b-a12b:free`
- 입력: 냉장고 재료 목록, 유통기한, 수량, 레시피 검색 정책
- 출력: JSON Schema를 만족하는 검색 단계 배열
- 저장 대상: PostgreSQL `recipe_search_plans`

### 3.3 장보기 목록 Agent

- 역할: 선택한 레시피와 냉장고 재고를 비교해 장보기 목록 생성
- 모델: `nvidia/nemotron-3-super-120b-a12b:free`
- 입력: 선택 레시피 재료, 냉장고 재고
- 출력: JSON Schema를 만족하는 장보기 항목 배열
- 저장 대상: PostgreSQL `shopping_list_runs`

### 3.4 Workflow 구성 Agent

- 역할: 레시피 step 데이터를 workflow 표현용 JSONL 구조로 정리
- 모델: `nvidia/nemotron-3-super-120b-a12b:free`
- 입력: 레시피 step 데이터
- 출력: JSONL step 레코드
- 저장 대상: `data/workflows/*.jsonl`

## 4. 냉장고 관리 요구사항

### 4.1 사용자 입력

- 입력 방식은 텍스트 기반 자연어 입력만 지원합니다.
- 날짜 표현은 `오늘`, `내일`, `모레`, `이번 주말`, `3월 18일`, `다음 주 화요일` 같은 자연어를 허용해야 합니다.
- 시간 단위는 추적하지 않고 날짜만 저장합니다.
- 수량이나 단위가 없는 입력은 기본값을 넣지 않습니다.
- 원문은 개인화와 추후 분석을 위해 별도로 저장합니다.

### 4.2 LLM 처리 방식

- 자연어 입력은 OpenRouter로 전송합니다.
- 냉장고 관리 agent는 JSON Schema에 맞는 응답만 반환해야 합니다.
- 응답이 스키마를 만족하지 않으면 애플리케이션 계층에서 저장하지 않고 사용자에게 수정 가능한 상태로 돌려줘야 합니다.
- 동일 재료라도 유통기한이 다르면 별도 row로 저장할 수 있어야 합니다.
- 유통기한이 없는 항목은 `null`로 저장하고, 추후 수정으로 언제든 채워 넣을 수 있어야 합니다.

### 4.3 고정 DB 스키마

#### `fridge_items`

- `id`: UUID
- `name`: 사용자 표시용 재료명
- `normalized_name`: 정규화 재료명
- `quantity`: 수량, nullable
- `unit`: 단위, nullable
- `expiry_date`: 날짜, nullable
- `days_left`: 정수, nullable
- `source_text_id`: 원문 로그 참조 ID
- `created_at`: 생성 시각
- `updated_at`: 수정 시각

#### `fridge_input_logs`

- `id`: UUID
- `raw_text`: 사용자 원문
- `parsed_json`: LLM 응답 원문 JSON
- `created_at`: 생성 시각

### 4.4 CRUD 요구사항

- 사용자는 재료를 추가할 수 있어야 합니다.
- 사용자는 저장된 재료를 수정할 수 있어야 합니다.
- 사용자는 저장된 재료를 삭제할 수 있어야 합니다.
- 목록은 표 형태로 보여야 합니다.
- 기본 정렬은 유통기한 임박순으로 합니다.
- 표 컬럼은 `재료명`, `수량`, `단위`, `유통기한`, `남은 일수`를 기본으로 노출합니다.

## 5. 레시피 추천 요구사항

### 5.1 레시피 검색 방식

- 추천은 단순 전체 매칭이 아니라 `검색 plan 기반 레시피 검색`으로 수행합니다.
- 레시피 검색 agent는 냉장고 재료 중 최대 5개를 주재료로 선택합니다.
- 1차 검색은 주재료 5개 조합으로 수행합니다.
- 1차 검색 결과가 부족하면 4개 조합으로 줄입니다.
- 이후 3개 조합으로 줄이며 검색 범위를 넓힙니다.
- 기본 검색 축소 순서는 `5 -> 4 -> 3`입니다.
- MVP에서는 2개 이하 조합 검색은 백로그로 남깁니다.

### 5.2 주재료 선택 기준

- 1순위는 유통기한이 임박한 재료입니다.
- 2순위는 수량이 충분한 재료입니다.
- 3순위는 레시피 DB에서 주재료로 자주 등장하는 재료입니다.
- agent는 각 단계에서 어떤 재료를 선택했는지와 왜 선택했는지를 plan으로 남겨야 합니다.

### 5.3 검색 대상 DB

- 외부 레시피 DB를 그대로 사용하지 않습니다.
- 외부 소스에서 검색한 레시피를 정제해 별도의 내부 레시피 DB를 구성합니다.
- MVP에서는 우선 예시 레시피 5개를 seed 데이터로 관리합니다.
- 레시피는 파싱하기 쉬운 구조화 형식으로 저장해야 합니다.

### 5.4 레시피 스키마

#### `recipes`

- `id`: UUID 또는 문자열 ID
- `title`: 레시피 이름
- `cuisine`: 나라 또는 분류, 예: `한식`, `일식`, `중식`, `양식`
- `summary`: 짧은 설명
- `servings`: 기준 인분
- `primary_ingredients`: 주재료 배열
- `required_ingredients`: 필수 재료 배열
- `optional_ingredients`: 추가 재료 배열
- `search_keywords`: 검색 키워드 배열
- `workflow_file`: 대응되는 workflow jsonl 경로
- `created_at`: 생성 시각
- `updated_at`: 수정 시각

#### ingredient item format

- `name`: 재료명
- `quantity`: 필요 수량
- `unit`: 단위
- `required`: 필수 여부

### 5.5 검색 plan 스키마

#### `recipe_search_plans`

- `id`: UUID
- `attempt_no`: 검색 시도 번호
- `selected_ingredients`: 현재 검색에 사용한 재료 배열
- `query_text`: 검색용 질의
- `reason`: 해당 조합을 선택한 이유
- `result_count`: 검색 결과 수
- `next_step`: 다음 검색 단계 설명
- `created_at`: 생성 시각

## 6. 장보기 목록 요구사항

### 6.1 생성 원칙

- 장보기 목록은 선택한 레시피 1개 기준으로 생성합니다.
- 냉장고에 없는 재료는 장보기 목록에 포함합니다.
- 냉장고에 재료가 있지만 수량이 부족한 경우도 장보기 목록에 포함합니다.
- 냉장고 보유 수량이 레시피 필요 수량의 절반 이하인 경우에는 `필수 구매`로 처리합니다.
- 이 판단 역시 장보기 목록 agent가 수행하되 JSON Schema에 맞는 결과를 반환해야 합니다.

### 6.2 장보기 목록 Agent 출력 스키마

- `name`: 재료명
- `required_quantity`: 레시피 기준 필요 수량
- `current_quantity`: 현재 냉장고 보유 수량
- `unit`: 단위
- `reason`: `missing`, `insufficient`, `half_or_less`
- `must_buy`: boolean

### 6.3 저장 구조

#### `shopping_list_runs`

- `id`: UUID
- `recipe_id`: 선택 레시피 ID
- `shopping_items`: JSON 배열
- `created_at`: 생성 시각

## 7. Workflow 요구사항

### 7.1 기본 원칙

- workflow는 검색된 레시피를 기반으로 단계적으로 생성되어야 합니다.
- 각 단계에는 소요 시간이 있어야 합니다.
- 각 단계에는 어떤 도구를 사용해야 하는지 있어야 합니다.
- 각 단계에는 사용자가 해야 할 작업 설명이 있어야 합니다.
- workflow는 JSONL 파일로 저장합니다.

### 7.2 Workflow JSONL 형식

- 파일 확장자는 `.jsonl`입니다.
- 한 줄은 하나의 step입니다.
- step은 `recipe_id`, `step_number`, `title`, `description`, `ingredients`, `tool`, `estimated_minutes`를 포함해야 합니다.
- `step_number`는 1부터 시작하는 정수입니다.
- 파일은 `step_number` 순서대로 읽어 workflow를 구성합니다.

### 7.3 화면 요구사항

- 사용자는 레시피 개요 화면을 먼저 봐야 합니다.
- 개요 화면에는 레시피명, 나라 분류, 전체 재료, 부족 재료, 총 단계 수, 총 예상 시간을 표시해야 합니다.
- workflow 화면은 한 번에 한 step만 보여줘야 합니다.
- 사용자는 이전과 다음 버튼으로 step을 이동해야 합니다.
- 마지막 step에서는 완료 버튼을 보여줘야 합니다.

## 8. 구현용 예시 데이터

### 8.1 레시피 seed 데이터

- 예시 레시피는 총 5개를 저장합니다.
- 예시 데이터는 `data/recipes.jsonl`에 저장합니다.
- 각 레시피에 대응되는 workflow는 `data/workflows/*.jsonl`에 저장합니다.

### 8.2 예시 레시피 구성 범위

- 한식 2개
- 일식 1개
- 중식 1개
- 양식 1개

## 9. 완료 기준

- 사용자가 자연어로 입력한 재료가 OpenRouter를 통해 구조화되어 PostgreSQL에 저장되어야 합니다.
- 사용자는 저장된 재료를 표에서 추가, 수정, 삭제할 수 있어야 합니다.
- 사용자 원문이 별도 로그 테이블에 저장되어야 합니다.
- 레시피 검색 agent가 5개 조합에서 시작해 4개, 3개 순으로 검색 범위를 줄이며 plan을 생성해야 합니다.
- 내부 레시피 DB에서 예시 레시피 5개가 구조화된 형태로 저장되어야 합니다.
- 선택 레시피에 대해 없는 재료와 절반 이하 재료가 장보기 목록에 포함되어야 합니다.
- workflow가 jsonl 기준으로 단계별 표현되고 각 step에 시간과 도구가 포함되어야 합니다.

## 10. 백로그

- 기능별 모델 다변화
- rate limit 대응
- timeout 대응
- OpenRouter 호출 실패 재시도 정책
- 운영 로그 및 호출 로그
- 2개 이하 재료 조합 검색
- 추천 결과 랭킹 고도화

## 11. 추가 확인 필요 사항

- `nemotron 3 super`를 계속 `:free` 버전으로 고정할지, 유료 모델로 전환 가능한 구조까지 바로 열어둘지 확인 필요
- PostgreSQL 접근 방식으로 ORM을 사용할지, SQL 중심으로 갈지 확인 필요
- `오늘`, `내일` 같은 자연어 날짜를 서버에서 1차 변환한 뒤 LLM에 넘길지, LLM이 전적으로 해석할지 확인 필요
- 레시피 검색 결과가 몇 건 미만일 때 `다음 단계 검색`으로 판단할지 임계값 확인 필요
- `절반 이하` 판단에서 단위가 다른 경우 변환 규칙을 둘지 확인 필요
- 외부 레시피를 어떤 기준으로 정제해 내부 DB에 넣을지 수집 기준 확인 필요
- workflow jsonl을 레시피 저장 시 미리 생성할지, 조회 시 동적으로 생성할지 확인 필요
