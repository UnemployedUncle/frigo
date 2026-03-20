# 요리 여정 핵심 MVP PRD

## 1. 목표

이 문서는 요리 여정의 첫 MVP를 실제로 개발하기 위한 기준 문서입니다. 현재 MVP는 아래 4개 흐름만 동작하고 테스트할 수 있으면 됩니다.

- 냉장고 자연어 입력 및 재료 관리
- 레시피 검색 계획 기반 추천
- 장보기 목록 생성
- 레시피 workflow 전환

## 2. 개발 진행 규칙

- 이 문서는 개발 진행 문서로 사용합니다.
- 각 구현 항목은 `[ ]` 또는 `[x]` 체크리스트로 관리합니다.
- 실제 코드, SQL, seed, 테스트가 확인된 항목만 `[x]`로 바꿉니다.
- 문서만 작성했거나 아이디어만 정리한 경우에는 완료 처리하지 않습니다.
- 기능 완료는 `구현 + 로컬 실행 확인 + 최소 검증`까지 끝났을 때만 인정합니다.

## 3. 고정 기술 결정

- [x] 모든 agent는 OpenRouter를 통해 동일한 LLM을 사용합니다.
- [x] 기본 모델은 `nvidia/nemotron-3-super-120b-a12b:free`로 고정합니다.
- [x] 추후 기능별 모델 다변화를 위해 agent별 모델 설정 구조를 분리합니다.
- [x] 현재 단계에서는 냉장고 관리 agent, 레시피 검색 agent, 장보기 목록 agent, workflow 구성 agent가 모두 같은 모델을 바라봅니다.
- [x] LLM 응답 형식은 `JSON Schema 강제` 방식으로 받습니다.
- [x] agent orchestration은 `LangChain`과 `LangGraph`로 구성합니다.
- [x] 영속 저장소는 `PostgreSQL`로 고정합니다.
- [x] PostgreSQL 접근은 ORM보다 `SQL 중심`으로 진행합니다.
- [x] 자연어 날짜 해석은 애플리케이션 전처리 대신 `LLM이 직접 해석`하는 방식으로 구성합니다.
- [ ] rate limit, timeout, 호출 실패, 운영 로그, 호출 로그는 이번 MVP 구현 범위에서 제외하고 백로그로 남깁니다.

## 4. Agent 구성

### 4.1 냉장고 관리 Agent

- [x] 역할: 자연어 입력을 고정 스키마의 재료 데이터로 변환
- [x] 모델: `nvidia/nemotron-3-super-120b-a12b:free`
- [x] 입력: 사용자 원문
- [x] 출력: JSON Schema를 만족하는 재료 배열
- [x] 저장 대상: PostgreSQL `fridge_items`, `fridge_input_logs`

### 4.2 레시피 검색 Plan Agent

- [x] 역할: 냉장고 재료에서 검색용 주재료를 뽑고 단계별 검색 plan 생성
- [x] 모델: `nvidia/nemotron-3-super-120b-a12b:free`
- [x] 입력: 냉장고 재료 목록, 유통기한, 수량, 레시피 검색 정책
- [x] 출력: JSON Schema를 만족하는 검색 단계 배열
- [x] 저장 대상: PostgreSQL `recipe_search_plans`

### 4.3 장보기 목록 Agent

- [x] 역할: 선택한 레시피와 냉장고 재고를 비교해 장보기 목록 생성
- [x] 모델: `nvidia/nemotron-3-super-120b-a12b:free`
- [x] 입력: 선택 레시피 재료, 냉장고 재고
- [x] 출력: JSON Schema를 만족하는 장보기 항목 배열
- [x] 저장 대상: PostgreSQL `shopping_list_runs`

### 4.4 Workflow 구성 Agent

- [x] 역할: 레시피 step 데이터를 workflow 표현용 JSONL 구조로 정리
- [x] 모델: `nvidia/nemotron-3-super-120b-a12b:free`
- [x] 입력: 레시피 step 데이터
- [x] 출력: JSONL step 레코드
- [x] 저장 대상: `data/workflows/*.jsonl`

## 5. 개발 착수 전 필수 체크

- [x] `.env`에 `OPENROUTER_API_KEY`가 존재합니다.
- [x] `.env`에 `OPENROUTER_BASE_URL`이 존재합니다.
- [ ] PostgreSQL 인스턴스에 접속 가능한 상태입니다.
- [x] `data/recipes.jsonl` 파일이 존재합니다.
- [x] `data/workflows/*.jsonl` 파일들이 존재합니다.
- [x] OpenRouter 예제 호출 코드가 로컬에서 참조 가능한 상태입니다.
- [x] 로컬에서 Python 실행 환경과 의존성 설치 방식이 정해져 있습니다.
- [x] SQL migration 파일을 저장할 위치가 정해져 있습니다.

## 6. 냉장고 관리 요구사항

### 6.1 사용자 입력

- [x] 입력 방식은 텍스트 기반 자연어 입력만 지원합니다.
- [x] 날짜 표현은 `오늘`, `내일`, `모레`, `이번 주말`, `3월 18일`, `다음 주 화요일` 같은 자연어를 허용해야 합니다.
- [x] 시간 단위는 추적하지 않고 날짜만 저장합니다.
- [x] 수량이나 단위가 없는 입력은 기본값을 넣지 않습니다.
- [x] 원문은 개인화와 추후 분석을 위해 별도로 저장합니다.

### 6.2 LLM 처리 방식

- [x] 자연어 입력은 OpenRouter로 전송합니다.
- [x] 냉장고 관리 agent는 JSON Schema에 맞는 응답만 반환해야 합니다.
- [ ] 응답이 스키마를 만족하지 않으면 애플리케이션 계층에서 저장하지 않고 사용자에게 수정 가능한 상태로 돌려줘야 합니다.
- [x] 동일 재료라도 유통기한이 다르면 별도 row로 저장할 수 있어야 합니다.
- [x] 유통기한이 없는 항목은 `null`로 저장하고, 추후 수정으로 언제든 채워 넣을 수 있어야 합니다.

### 6.3 고정 DB 스키마

#### `fridge_items`

- [x] `id`: UUID
- [x] `name`: 사용자 표시용 재료명
- [x] `normalized_name`: 정규화 재료명
- [x] `quantity`: 수량, nullable
- [x] `unit`: 단위, nullable
- [x] `expiry_date`: 날짜, nullable
- [x] `days_left`: 정수, nullable
- [x] `source_text_id`: 원문 로그 참조 ID
- [x] `created_at`: 생성 시각
- [x] `updated_at`: 수정 시각

#### `fridge_input_logs`

- [x] `id`: UUID
- [x] `raw_text`: 사용자 원문
- [x] `parsed_json`: LLM 응답 원문 JSON
- [x] `created_at`: 생성 시각

### 6.4 CRUD 요구사항

- [x] 사용자는 재료를 추가할 수 있어야 합니다.
- [x] 사용자는 저장된 재료를 수정할 수 있어야 합니다.
- [x] 사용자는 저장된 재료를 삭제할 수 있어야 합니다.
- [x] 목록은 표 형태로 보여야 합니다.
- [x] 기본 정렬은 유통기한 임박순으로 합니다.
- [x] 표 컬럼은 `재료명`, `수량`, `단위`, `유통기한`, `남은 일수`를 기본으로 노출합니다.

## 7. 레시피 추천 요구사항

### 7.1 레시피 검색 방식

- [x] 추천은 단순 전체 매칭이 아니라 `검색 plan 기반 레시피 검색`으로 수행합니다.
- [x] 레시피 검색 agent는 냉장고 재료 중 최대 5개를 주재료로 선택합니다.
- [x] 1차 검색은 주재료 5개 조합으로 수행합니다.
- [x] 검색 결과가 1건도 없으면 4개 조합으로 줄입니다.
- [x] 4개 조합에서도 결과가 1건도 없으면 3개 조합으로 줄입니다.
- [x] 기본 검색 축소 순서는 `5 -> 4 -> 3`입니다.
- [x] 5개 조합 검색 결과가 10개 이상이면 재료를 1개 더 추가한 6개 조합으로 다시 검색해 범위를 좁힙니다.
- [x] 6개 조합 재검색은 냉장고에 6번째 후보 재료가 있을 때만 수행합니다.
- [ ] MVP에서는 2개 이하 조합 검색은 백로그로 남깁니다.

### 7.2 주재료 선택 기준

- [x] 1순위는 유통기한이 임박한 재료입니다.
- [x] 2순위는 수량이 충분한 재료입니다.
- [x] 3순위는 레시피 DB에서 주재료로 자주 등장하는 재료입니다.
- [x] agent는 각 단계에서 어떤 재료를 선택했는지와 왜 선택했는지를 plan으로 남겨야 합니다.

### 7.3 검색 대상 DB

- [x] 외부 레시피 DB를 그대로 사용하지 않습니다.
- [ ] 외부 소스에서 검색한 레시피를 정제해 별도의 내부 레시피 DB를 구성합니다.
- [ ] 외부 레시피 정제 후 내부 DB 반영은 MVP 단계에서 1차례만 수행합니다.
- [x] MVP에서는 우선 예시 레시피 5개를 seed 데이터로 관리합니다.
- [x] 레시피는 파싱하기 쉬운 구조화 형식으로 저장해야 합니다.

### 7.4 레시피 스키마

#### `recipes`

- [x] `id`: UUID 또는 문자열 ID
- [x] `title`: 레시피 이름
- [x] `cuisine`: 나라 또는 분류, 예: `한식`, `일식`, `중식`, `양식`
- [x] `summary`: 짧은 설명
- [x] `servings`: 기준 인분
- [x] `primary_ingredients`: 주재료 배열
- [x] `required_ingredients`: 필수 재료 배열
- [x] `optional_ingredients`: 추가 재료 배열
- [x] `search_keywords`: 검색 키워드 배열
- [x] `workflow_file`: 대응되는 workflow jsonl 경로
- [x] `created_at`: 생성 시각
- [x] `updated_at`: 수정 시각

#### ingredient item format

- [x] `name`: 재료명
- [x] `quantity`: 필요 수량
- [x] `unit`: 단위
- [x] `required`: 필수 여부

### 7.5 검색 plan 스키마

#### `recipe_search_plans`

- [x] `id`: UUID
- [x] `attempt_no`: 검색 시도 번호
- [x] `selected_ingredients`: 현재 검색에 사용한 재료 배열
- [x] `query_text`: 검색용 질의
- [x] `reason`: 해당 조합을 선택한 이유
- [x] `result_count`: 검색 결과 수
- [x] `next_step`: 다음 검색 단계 설명
- [x] `created_at`: 생성 시각

## 8. 장보기 목록 요구사항

### 8.1 생성 원칙

- [x] 장보기 목록은 선택한 레시피 1개 기준으로 생성합니다.
- [x] 냉장고에 없는 재료는 장보기 목록에 포함합니다.
- [x] 냉장고에 재료가 있지만 수량이 부족한 경우도 장보기 목록에 포함합니다.
- [x] 냉장고 보유 수량이 레시피 필요 수량의 절반 이하인 경우에는 `필수 구매`로 처리합니다.
- [x] 이 판단 역시 장보기 목록 agent가 수행하되 JSON Schema에 맞는 결과를 반환해야 합니다.

### 8.2 장보기 목록 Agent 출력 스키마

- [x] `name`: 재료명
- [x] `required_quantity`: 레시피 기준 필요 수량
- [x] `current_quantity`: 현재 냉장고 보유 수량
- [x] `unit`: 단위
- [x] `reason`: `missing`, `insufficient`, `half_or_less`
- [x] `must_buy`: boolean

### 8.3 저장 구조

#### `shopping_list_runs`

- [x] `id`: UUID
- [x] `recipe_id`: 선택 레시피 ID
- [x] `shopping_items`: JSON 배열
- [x] `created_at`: 생성 시각

## 9. Workflow 요구사항

### 9.1 기본 원칙

- [x] workflow는 검색된 레시피를 기반으로 단계적으로 생성되어야 합니다.
- [x] 각 단계에는 소요 시간이 있어야 합니다.
- [x] 각 단계에는 어떤 도구를 사용해야 하는지 있어야 합니다.
- [x] 각 단계에는 사용자가 해야 할 작업 설명이 있어야 합니다.
- [x] workflow는 JSONL 파일로 저장합니다.
- [x] workflow jsonl은 레시피별로 미리 생성해 둡니다.

### 9.2 Workflow JSONL 형식

- [x] 파일 확장자는 `.jsonl`입니다.
- [x] 한 줄은 하나의 step입니다.
- [x] step은 `recipe_id`, `step_number`, `title`, `description`, `ingredients`, `tool`, `estimated_minutes`를 포함해야 합니다.
- [x] `step_number`는 1부터 시작하는 정수입니다.
- [x] 파일은 `step_number` 순서대로 읽어 workflow를 구성합니다.

### 9.3 화면 요구사항

- [x] 사용자는 레시피 개요 화면을 먼저 봐야 합니다.
- [x] 개요 화면에는 레시피명, 나라 분류, 전체 재료, 부족 재료, 총 단계 수, 총 예상 시간을 표시해야 합니다.
- [x] workflow 화면은 한 번에 한 step만 보여줘야 합니다.
- [x] 사용자는 이전과 다음 버튼으로 step을 이동해야 합니다.
- [x] 마지막 step에서는 완료 버튼을 보여줘야 합니다.

## 10. 구현용 예시 데이터

### 10.1 레시피 seed 데이터

- [x] 예시 레시피는 총 5개를 저장합니다.
- [x] 예시 데이터는 `data/recipes.jsonl`에 저장합니다.
- [x] 각 레시피에 대응되는 workflow는 `data/workflows/*.jsonl`에 저장합니다.

### 10.2 예시 레시피 구성 범위

- [x] 한식 2개
- [x] 일식 1개
- [x] 중식 1개
- [x] 양식 1개

## 11. 최소 API/입출력 체크

### 11.1 냉장고

- [x] `POST /fridge/parse`: 자연어 입력을 받아 재료 저장 결과를 반환해야 합니다.
- [x] `GET /fridge/items`: 저장된 재료 목록을 반환해야 합니다.
- [x] `PATCH /fridge/items/:id`: 재료 수정이 가능해야 합니다.
- [x] `DELETE /fridge/items/:id`: 재료 삭제가 가능해야 합니다.

### 11.2 추천

- [x] `POST /recipes/recommend`: 검색 plan과 추천 레시피를 반환해야 합니다.
- [x] 결과 0건 시 4개, 3개 fallback 여부를 응답 또는 로그로 확인할 수 있어야 합니다.
- [x] 결과 10건 이상 시 6개 조합 재검색 분기를 확인할 수 있어야 합니다.

### 11.3 장보기

- [x] `POST /shopping-list`: 선택 레시피 기준 장보기 목록을 반환해야 합니다.
- [x] `must_buy` 값과 `reason` 값이 응답에서 검증 가능해야 합니다.

### 11.4 Workflow

- [x] `GET /recipes/:id/workflow`: 레시피의 workflow step 목록을 반환해야 합니다.
- [x] step_number 순서가 보장되어야 합니다.

## 12. 수동 Smoke Test 시나리오

- [ ] `시금치 1봉지 내일, 새우 200g 오늘` 입력 시 냉장고 표 저장 확인
- [ ] 냉장고 조회 후 수량 수정 확인
- [ ] 냉장고 항목 삭제 확인
- [ ] 추천 결과 0건 케이스에서 5 -> 4 -> 3 fallback 확인
- [ ] 추천 결과 10건 이상 케이스에서 6개 조합 재검색 확인
- [ ] 장보기 목록에서 없는 재료 포함 확인
- [ ] 장보기 목록에서 절반 이하 재고 `must_buy=true` 확인
- [ ] workflow jsonl 로드 확인
- [ ] workflow 첫 단계 이동 확인
- [ ] workflow 중간 단계 이동 확인
- [ ] workflow 마지막 단계 완료 확인

## 13. 완료 기준

- [ ] 사용자가 자연어로 입력한 재료가 OpenRouter를 통해 구조화되어 PostgreSQL에 저장됩니다.
- [ ] 사용자는 저장된 재료를 표에서 추가, 수정, 삭제할 수 있습니다.
- [ ] 사용자 원문이 별도 로그 테이블에 저장됩니다.
- [ ] 레시피 검색 agent가 5개 조합에서 시작하고, 결과가 0건이면 4개와 3개 순으로 검색 범위를 줄입니다.
- [ ] 레시피 검색 결과가 10건 이상이면 6개 조합 재검색으로 범위를 좁힙니다.
- [ ] 내부 레시피 DB에서 예시 레시피 5개가 구조화된 형태로 저장됩니다.
- [ ] 선택 레시피에 대해 없는 재료와 절반 이하 재료가 장보기 목록에 포함됩니다.
- [ ] workflow가 레시피별 jsonl 기준으로 단계별 표현되고 각 step에 시간과 도구가 포함됩니다.

## 14. 개발 순서 및 전체 To-do List

### 14.1 공통 영역

- [x] OpenRouter 공통 클라이언트 래퍼를 만듭니다.
- [x] Nemotron 3 Super Free 모델 상수를 agent별 설정 구조로 분리합니다.
- [x] JSON Schema 응답 강제 유틸리티를 만듭니다.
- [x] LangChain 공통 prompt/response parser 계층을 만듭니다.
- [x] LangGraph 공통 graph 실행 구조를 만듭니다.
- [x] PostgreSQL 연결 계층과 SQL 실행 유틸리티를 만듭니다.
- [x] SQL 마이그레이션 기준 파일을 만듭니다.

### 14.2 데이터 계층

- [x] `fridge_items` 테이블을 생성합니다.
- [x] `fridge_input_logs` 테이블을 생성합니다.
- [x] `recipes` 테이블 또는 seed 적재용 구조를 생성합니다.
- [x] `recipe_search_plans` 테이블을 생성합니다.
- [x] `shopping_list_runs` 테이블을 생성합니다.
- [x] `data/recipes.jsonl` seed 적재 스크립트를 만듭니다.
- [x] `data/workflows/*.jsonl` 유효성 검사 스크립트를 만듭니다.

### 14.3 냉장고 관리 기능

- [x] 자연어 입력 API를 만듭니다.
- [x] 냉장고 관리 agent prompt와 JSON Schema를 확정합니다.
- [x] OpenRouter 응답 검증 후 DB 저장 흐름을 구현합니다.
- [x] 사용자 원문 저장 흐름을 구현합니다.
- [x] 냉장고 목록 조회 SQL을 구현합니다.
- [x] 냉장고 추가, 수정, 삭제 SQL API를 구현합니다.
- [x] 유통기한 기반 `days_left` 계산 로직을 구현합니다.

### 14.4 레시피 추천 기능

- [x] 주재료 후보 선택 로직을 구현합니다.
- [x] 5개 조합 1차 검색 plan 생성을 구현합니다.
- [x] 결과 0건일 때 4개 조합 fallback을 구현합니다.
- [x] 결과 0건일 때 3개 조합 fallback을 구현합니다.
- [x] 결과 10건 이상일 때 6개 조합 재검색을 구현합니다.
- [x] 검색 plan 저장 SQL을 구현합니다.
- [x] 추천 결과 정렬과 중복 제거를 구현합니다.

### 14.5 장보기 목록 기능

- [x] 선택 레시피와 냉장고 재고 비교 로직을 구현합니다.
- [x] 없는 재료 판별 로직을 구현합니다.
- [x] 부족 수량 판별 로직을 구현합니다.
- [x] 절반 이하 재고의 `must_buy` 판별 로직을 구현합니다.
- [x] 장보기 목록 agent prompt와 JSON Schema를 구현합니다.
- [x] 장보기 결과 저장 SQL을 구현합니다.

### 14.6 Workflow 기능

- [x] 레시피별 workflow jsonl 로더를 구현합니다.
- [x] step_number 기준 정렬 및 검증 로직을 구현합니다.
- [x] 레시피 개요 데이터 조합 로직을 구현합니다.
- [x] 이전, 다음, 완료 흐름 상태 관리를 구현합니다.
- [x] 레시피와 workflow jsonl 경로 매핑을 구현합니다.

### 14.7 통합 및 검증

- [ ] 냉장고 입력부터 추천까지 E2E 흐름을 검증합니다.
- [ ] 추천부터 장보기 목록 생성까지 E2E 흐름을 검증합니다.
- [ ] 레시피 선택부터 workflow 완료까지 E2E 흐름을 검증합니다.
- [ ] 예시 레시피 5개 기준 시나리오 테스트를 작성합니다.
- [ ] JSON Schema 응답 실패 시 fallback UX를 점검합니다.

## 15. 완료 표시 규칙

- [ ] 체크리스트 항목은 코드, SQL, seed, 테스트 또는 수동 검증 중 최소 하나로 확인된 뒤 완료 처리합니다.
- [ ] 상위 섹션은 하위 필수 항목이 모두 완료되었을 때만 완료로 간주합니다.
- [ ] Smoke test 항목은 실제 입력값으로 최소 1회 실행한 뒤 완료 처리합니다.
- [ ] 완료 기준 섹션은 기능이 실제로 end-to-end 동작할 때만 체크합니다.

## 16. 백로그

- [ ] 기능별 모델 다변화
- [ ] rate limit 대응
- [ ] timeout 대응
- [ ] OpenRouter 호출 실패 재시도 정책
- [ ] 운영 로그 및 호출 로그
- [ ] 2개 이하 재료 조합 검색
- [ ] 추천 결과 랭킹 고도화

## 17. 추가 확인 필요 사항

- [ ] `절반 이하` 판단에서 단위가 다른 경우 변환 규칙을 둘지 확인 필요
- [ ] 외부 레시피를 어떤 기준으로 정제해 내부 DB에 넣을지 수집 기준 확인 필요
- [ ] 6개 조합 재검색에서도 결과가 너무 많은 경우 최종 노출 개수를 어떻게 제한할지 확인 필요
- [ ] recipe seed 적재를 SQL insert 기반으로 할지, 별도 import script 기반으로 할지 확인 필요
