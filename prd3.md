# 요리 여정 PRD v3

## 1. 문서 목적

이 문서는 현재 구현된 text-first 서비스 위에서 다음 단계의 제품 요구사항을 고정하기 위한 문서입니다.

이번 버전의 핵심 목적은 아래 3가지입니다.

- Home 추천을 냉장고 기반 추천이 아니라 `무작위 8개 추천`으로 단순화합니다.
- 냉장고 기반 추천은 별도 화면으로 분리하고, 사용자가 직접 재료 5개를 골라 추천을 받게 합니다.
- Cook Mode의 단계별 타이머가 실제로 자동 진행되어, 전체 레시피 시간이 총합 시간 안에 끝나도록 만듭니다.

추가로 이번 버전은 `서비스를 가볍게 만들어 빠르게 써보고 피드백을 넣을 수 있는 상태`를 목표로 합니다.

이 문서는 [prd.md](/Users/yongsupyi/Desktop/frigo/prd.md)와 [prd2.md](/Users/yongsupyi/Desktop/frigo/prd2.md)를 이어받는 실행 문서입니다.

## 2. 이번 버전 목표

이번 버전의 사용자 흐름은 아래와 같습니다.

1. Home에서 무작위 레시피 8개를 가볍게 탐색합니다.
2. Fridge에서 자연어 입력과 재료 관리를 수행합니다.
3. Fridge에서 재료 5개를 직접 선택해 냉장고 기반 추천 화면으로 이동합니다.
4. 추천 화면에서 1~8개의 레시피 후보를 확인하고, 마음에 드는 레시피는 별표로 저장합니다.
5. 레시피 상세로 들어가 재료, 장보기 목록, 전체 workflow를 확인합니다.
6. Cook Mode에서 step이 자동으로 넘어가며 전체 조리가 끝나면 완료 기록이 저장됩니다.
7. 저장하거나 완료한 레시피 수는 Home 화면에 숫자로 반영됩니다.

이번 버전의 성능 목표는 아래와 같습니다.

- Home은 가볍게 열려야 합니다.
- Fridge는 즉시 입력/수정 가능한 속도를 유지해야 합니다.
- Recipe Detail은 진입 즉시 읽을 수 있어야 합니다.
- Cook Mode는 서버 round-trip 없이 브라우저 내에서 자연스럽게 흘러가야 합니다.

## 3. 핵심 변경 사항

### 3.1 Home 추천 변경

Home은 더 이상 냉장고 기반 추천을 보여주지 않습니다.

- Home의 추천 섹션은 `Random Recipes 8`로 변경합니다.
- 추천 수는 항상 최대 8개입니다.
- 추천 기준은 냉장고 재료가 아니라 무작위 선택입니다.
- Home의 추천 카드는 현재와 동일하게 `제목`, `한 줄 설명`, `핵심 재료`, `View Recipe`를 표시합니다.
- Home은 여전히 `Cooking Grass + 레시피 카드`만 보여줍니다.

무작위 추천 구현 원칙:

- 대용량 DB에서 `ORDER BY RANDOM()` 전체 스캔은 사용하지 않습니다.
- Postgres large-table-safe sampling 방식으로 8개를 채웁니다.
- 1차 시도에서 8개가 모이지 않으면 sampling을 한 번 더 수행하고, 그래도 부족하면 `id ASC` 기준으로 나머지를 채웁니다.
- 결과는 중복 없이 8개까지 보여줍니다.

### 3.2 냉장고 기반 추천 화면 분리

냉장고 기반 추천은 별도 화면으로 분리합니다.

새 흐름:

- `/fridge` 화면에서 현재 재료 목록에 선택 체크 UI를 추가합니다.
- 사용자는 추천용 재료를 선택한 뒤 `Recommend From Fridge` 버튼으로 이동합니다.
- 새 화면은 `/recommendations/fridge`를 사용합니다.

선택 규칙:

- 냉장고에 5개 이상 재료가 있으면 정확히 5개를 선택해야 합니다.
- 냉장고에 5개 미만 재료가 있으면 보유한 재료 전체를 선택할 수 있습니다.
- 0개 선택 또는 6개 이상 선택은 허용하지 않습니다.
- 서버는 선택된 `fridge_item.id` 목록을 기준으로 재료를 확정합니다.

추천 로직 규칙:

- 이 화면에서는 기존 추천 로직의 “재료 선택 단계”를 사용자 선택으로 대체합니다.
- 즉, `selected_ingredients`는 agent가 고르지 않고 사용자가 고른 재료를 그대로 사용합니다.
- 이후 단계는 현재 추천 엔진의 overlap 검색, fallback, 점수화 로직을 그대로 사용합니다.
- 결과는 최소 1개, 최대 8개를 목표로 합니다.
- 결과가 0개면 fallback 규칙에 따라 overlap 조건을 완화하거나 선택 재료 일부를 줄이지 않고, 먼저 기존 minimum overlap 정책만 완화합니다.
- 그래도 0개면 빈 결과와 안내 문구를 보여줍니다.

화면 요구사항:

- 선택한 재료 5개를 상단에 텍스트로 다시 보여줍니다.
- 추천 결과 카드 1~8개를 보여줍니다.
- 각 카드에는 `제목`, `한 줄 설명`, `핵심 재료`, `View Recipe`를 표시합니다.
- Home과 다르게 이 화면은 냉장고 선택 기반 추천 결과라는 점을 명확히 표시합니다.

### 3.3 Cook Mode 타이머 수정

현재 문제는 step별 타이머가 실제로 연속 실행되지 않아, 총 조리 시간이 의도한 전체 시간 안에 흐르지 않는 점입니다.

새 규칙:

- 레시피 총 시간은 `sum(step.estimated_seconds)`로 고정합니다.
- Cook Mode는 현재 step 하나만 보여주되, step 타이머가 0이 되면 자동으로 다음 step으로 이동합니다.
- 마지막 step이 끝나면 즉시 완료 처리합니다.
- 예를 들어 총 40초 레시피라면 각 step의 `estimated_seconds` 총합이 40이어야 하며, 전체 조리는 40초 안에 끝나야 합니다.

타이머 동작 규칙:

- 진입 시 첫 step 타이머가 자동 시작됩니다.
- `Pause`는 현재 step과 전체 남은 시간 모두 멈춥니다.
- `Resume`은 멈춘 시점부터 다시 시작합니다.
- `Stop`은 상세 화면으로 돌아가며 완료 기록을 저장하지 않습니다.
- `Complete Now`는 현재 남은 시간을 무시하고 즉시 완료 기록을 저장합니다.
- 새로고침 없이 같은 페이지에서 step 전환이 일어나야 합니다.
- step 전환 시 별도 서버 round-trip 없이 브라우저 내 상태로 이동합니다.
- 마지막 완료 시점에만 `/cook/{recipe_id}/complete`를 호출합니다.

시간 데이터 규칙:

- workflow의 단일 source of truth는 `estimated_seconds`입니다.
- UI에 표시되는 총 시간도 `estimated_seconds` 총합에서 계산합니다.
- `estimated_minutes`는 더 이상 타이머 계산에 사용하지 않습니다.

### 3.4 피드백 저장 방식

빠른 피드백 수집을 위해 사용자가 레시피를 가볍게 평가할 수 있어야 합니다.

기본 규칙:

- 사용자는 레시피 카드나 상세 화면에서 `별표`로 레시피를 저장할 수 있습니다.
- 별표 저장은 “마음에 든 레시피”를 뜻하며, 조리를 완료하지 않아도 남길 수 있습니다.
- 조리를 끝낸 레시피는 완료 기록으로 따로 저장됩니다.
- Home은 아래 숫자를 함께 보여줍니다.
  - `Saved Recipes`: 별표 저장한 레시피 수
  - `Completed Recipes`: 완료한 레시피 수

데이터 규칙:

- 별표 저장과 완료 기록은 서로 독립입니다.
- 같은 레시피를 여러 번 완료할 수 있습니다.
- 별표 저장은 레시피당 1회 상태만 유지합니다.
- Home 숫자는 누적 카운트 기준으로 표시합니다.

UI 규칙:

- Home 상단에는 잔디와 함께 숫자 요약 블록을 둡니다.
- 추천 카드에는 `Save` 또는 `★` 토글을 둡니다.
- Recipe Detail에도 동일한 저장 액션을 둡니다.

### 3.5 리팩토링 및 경량화 원칙

이번 버전에서 기능 추가와 함께 반드시 적용할 경량화 원칙은 아래와 같습니다.

- UI 경로는 `fallback-first`를 유지합니다.
- Home, Fridge Recommendation, Recipe Detail은 기본적으로 OpenRouter를 호출하지 않습니다.
- 단순 정렬/검증/선택 로직은 agent graph 대신 일반 Python 함수로 우선 구현합니다.
- 대용량 DB에서는 전체 스캔이나 `ORDER BY RANDOM()` 같은 비효율 쿼리를 피합니다.
- recommendation, shopping, workflow는 각각 `조회`, `계산`, `렌더링` 책임을 분리합니다.
- 테스트는 기본 경로와 대용량 smoke 경로를 분리해, 빠른 피드백 루프를 유지합니다.

## 4. 성능 및 리팩토링 요구사항

### 4.1 목표 응답 속도

이번 버전 목표:

- Home: 체감상 즉시 열려야 하며, 서버 렌더 기준 수초 이하를 목표로 합니다.
- Fridge: 자연어 입력 전 기본 페이지는 매우 빠르게 열려야 합니다.
- Recipe Detail: LLM 호출 없이 즉시 렌더되어야 합니다.
- Cook Mode: step 전환은 브라우저 상태만으로 수행되어야 합니다.

### 4.2 우선 리팩토링 대상

- Home 추천 경로
  - 무작위 8개 조회 전용 repository 메서드 추가
  - 냉장고 기반 추천 호출 제거
- Fridge Recommendation 경로
  - 사용자가 선택한 재료를 그대로 서비스 입력으로 사용
  - 기존 “재료 선택 agent” 단계 우회
- Shopping 계산 경로
  - Recipe Detail 진입 시 fallback-safe 계산만 사용
  - 화면 렌더와 저장(persist) 분리
- Workflow / Cook Mode 경로
  - 타이머 로직을 브라우저 상태 중심으로 재구성
  - step 전환 시 서버 요청 제거
- 레거시 경계 정리
  - `workflow_file`는 deprecated 상태 유지
  - `estimated_minutes`는 표시/계산 주 경로에서 제거
  - `data/workflows`는 runtime 비의존 상태 유지

### 4.3 비효율 제거 원칙

- 대용량 recipe 테이블에서 전체 로드 금지
- recommendation은 candidate-first 조회만 허용
- UI에서 plan step 저장 같은 부수효과는 최소화
- 테스트 기본 경로에서는 대용량 seed 전체 line count 금지
- build/restart 없이 검증 가능한 테스트클라이언트 기반 검증 경로 유지

### 4.4 코드 정리 원칙

- `main.py`는 화면 조합과 route 중심으로 유지하되, 서비스 정책 분기는 서비스 계층으로 내립니다.
- `RecipeService`는 `random_home_recipes`, `recommend_from_selected_items`, `agent_based_recommend` 성격으로 책임을 분리합니다.
- `ShoppingService`는 `계산`과 `저장`을 분리합니다.
- `Cook Mode`는 template + 최소 API 호출 구조로 단순화합니다.
- 문서/테스트/스키마에서 deprecated 필드를 계속 주 경로처럼 다루지 않게 정리합니다.

## 5. 화면 구조

### 4.1 Home (`/`)

- `Cooking Grass`
- `Saved Recipes` 숫자
- `Completed Recipes` 숫자
- `Random Recipes 8`

Home에는 아래를 두지 않습니다.

- 냉장고 기반 추천
- 재료 선택 UI
- 자연어 입력
- 편집 테이블

### 4.2 Fridge (`/fridge`)

기존 요소를 유지합니다.

- 자연어 입력
- parsed preview
- text fridge
- 편집 테이블

추가 요소:

- 추천용 체크박스 또는 선택 컨트롤
- `Recommend From Fridge` 버튼
- 선택 개수 표시 (`0/5`, `3/5` 등)

### 4.3 Fridge Recommendation (`/recommendations/fridge`)

새 화면입니다.

- 상단: 선택한 재료 5개 요약
- 본문: 추천 결과 1~8개 카드
- 하단 또는 상단 액션: `Back to Fridge`
- 각 카드: `Save` 또는 `★` 토글

### 4.4 Recipe Detail (`/recipes/{recipe_id}`)

기존 구조를 유지합니다.

- 저장 액션 (`Save` / `★`)
- 전체 재료
- shopping list
- 전체 workflow
- `Start Cooking`

### 4.5 Cook Mode (`/cook/{recipe_id}`)

기존 text-first UI를 유지하되 타이머 동작을 수정합니다.

- 현재 step
- step 남은 시간
- 전체 남은 시간
- `Pause`
- `Resume`
- `Stop`
- `Complete Now`

## 6. 라우트 및 인터페이스

유지:

- `GET /`
- `GET /fridge`
- `GET /recipes/{recipe_id}`
- `GET /cook/{recipe_id}`
- `POST /cook/{recipe_id}/complete`

추가:

- `POST /ui/recommend/from-fridge`
  - 입력: `selected_item_ids`
  - 역할: 선택된 냉장고 재료 검증 후 추천 화면으로 이동
- `GET /recommendations/fridge`
  - 입력: 서버가 해석 가능한 선택 재료 컨텍스트
  - 출력: 선택 재료 요약 + 추천 결과 1~8개
- `POST /recipes/{recipe_id}/save`
  - 역할: 별표 저장 토글
- `GET /feedback/summary`
  - 역할: Home 숫자 요약 데이터 제공 또는 내부 조합용 helper

추천 서비스 요구사항:

- Home용 `random recipes` 조회 메서드 필요
- 사용자 선택 재료 기반 `recommend_from_selected_items(...)` 메서드 필요
- 기존 `recommend(...)`는 agent-selection 기반 추천으로 유지
- Home 추천과 냉장고 기반 추천은 서로 다른 서비스 entrypoint로 분리합니다.

Cook Mode 인터페이스 요구사항:

- 각 step의 `estimated_seconds`
- 전체 합계 `total_seconds`
- 브라우저 내 `remaining_total_seconds`
- 브라우저 내 `remaining_step_seconds`

피드백 데이터 요구사항:

- `saved_recipes` 또는 동등한 저장 테이블 필요
- `recipe_id`
- `saved_at`
- Home용 `saved_count`, `completed_count` 집계 경로 필요

## 7. 구현 체크리스트

### 7.1 Home

- [x] Home 추천을 무작위 8개로 변경합니다.
- [x] Home 추천에서 냉장고 기반 로직을 제거합니다.
- [x] 대용량 DB 기준으로 무작위 8개를 빠르게 가져오는 repository 경로를 추가합니다.
- [x] Home 경로에서 LLM 호출이 일어나지 않도록 고정합니다.
- [x] Home에 `Saved Recipes`, `Completed Recipes` 숫자 요약을 추가합니다.

### 7.2 Fridge

- [x] 재료 선택 UI를 추가합니다.
- [x] 5개 선택 규칙 검증을 추가합니다.
- [x] 선택 재료 기반 추천 화면으로 이동하는 form/action을 추가합니다.

### 7.3 Recommendation Screen

- [x] `/recommendations/fridge` 템플릿을 추가합니다.
- [x] 선택된 냉장고 재료를 그대로 추천 입력으로 사용하는 service 경로를 구현합니다.
- [x] 추천 결과를 1~8개 카드로 렌더링합니다.
- [x] 이 화면에서도 기본적으로 LLM을 호출하지 않도록 합니다.
- [x] 추천 카드에 저장 토글을 추가합니다.

### 7.4 Cook Mode

- [x] 현재 template의 타이머가 step별 자동 전환을 실제로 수행하도록 수정합니다.
- [x] 전체 남은 시간과 현재 step 시간이 함께 동작하도록 수정합니다.
- [x] 마지막 step 종료 시 자동 완료 요청이 발생하도록 수정합니다.
- [x] `Pause / Resume / Stop / Complete Now` 동작이 실제 타이머 상태와 일치하도록 맞춥니다.

### 7.5 Feedback

- [x] 별표 저장용 테이블/저장 구조를 추가합니다.
- [x] 레시피 카드와 상세 화면에서 저장 토글을 구현합니다.
- [x] Home 숫자 요약 집계를 구현합니다.
- [x] 저장 수와 완료 수를 분리해 노출합니다.

### 7.6 리팩토링 / 정리

- [x] Home / Detail / Recommendation 경로의 fallback-first 정책을 코드로 고정합니다.
- [x] recommendation 관련 서비스 메서드를 역할별로 분리합니다.
- [x] shopping 계산과 저장을 분리합니다.
- [x] deprecated 필드(`workflow_file`, `estimated_minutes`)가 주 경로에 영향을 주지 않도록 정리합니다.
- [x] 테스트를 기본 빠른 세트와 대용량 smoke 세트로 유지합니다.

## 8. 구현 순서 작업 리스트

### 8.1 P0 - 빠른 피드백 가능한 최소 흐름

- [x] Home 랜덤 8 추천으로 전환
- [x] Home 숫자 요약(`Saved Recipes`, `Completed Recipes`) 추가
- [x] Fridge에서 재료 5개 선택 UI 추가
- [x] `/recommendations/fridge` 화면 추가
- [x] 선택 재료 기반 추천 결과 1~8개 렌더링
- [x] 추천 카드 저장 토글 구현
- [x] Detail 화면 저장 토글 구현

완료 기준:

- Home이 가볍게 열려야 합니다.
- 사용자가 레시피를 저장하고 Home 숫자 증가를 바로 확인할 수 있어야 합니다.
- Fridge에서 재료를 고른 뒤 추천 화면으로 이동할 수 있어야 합니다.

### 8.2 P1 - Cook Mode 정상화

- [x] step별 자동 타이머 전환 구현
- [x] 전체 남은 시간 표시 추가
- [x] 마지막 step 자동 완료 구현
- [x] 완료 시 `Completed Recipes` 숫자 반영

완료 기준:

- 예시 40초 레시피가 step 합계 기준으로 40초 안에 종료되어야 합니다.
- 완료 후 Home 숫자가 증가해야 합니다.

### 8.3 P2 - 구조 정리 및 경량화

- [x] 추천 service 책임 분리
- [x] shopping 계산/저장 분리
- [x] UI 경로 fallback-first 고정
- [x] deprecated 필드 영향 제거
- [x] 빠른 테스트 세트와 smoke 세트 유지

현재 구현 메모:

- Home은 랜덤 8 카드와 저장/완료 숫자를 보여줍니다.
- Fridge는 5개 선택 추천 폼을 제공합니다.
- `/recommendations/fridge`는 선택 재료 기반 추천 결과를 렌더링합니다.
- Cook Mode는 브라우저 내 전체 workflow 상태를 관리합니다.
- 저장 상태는 `saved_recipes`, 완료 상태는 `cooking_sessions`에 반영됩니다.

완료 기준:

- 기본 테스트가 빠르게 끝나야 합니다.
- Home / Recommendation / Detail 경로에서 고비용 LLM 호출이 기본값으로 일어나지 않아야 합니다.

## 9. 테스트 계획

- [ ] Home은 항상 무작위 레시피 최대 8개를 보여줘야 합니다.
- [ ] Home은 냉장고 데이터 유무와 관계없이 추천 8개를 보여줄 수 있어야 합니다.
- [ ] Home은 `Saved Recipes`, `Completed Recipes` 숫자를 보여줘야 합니다.
- [ ] `/fridge`에서 5개 선택 후 추천 화면으로 이동해야 합니다.
- [ ] 5개 이상 선택 시 검증 에러가 보여야 합니다.
- [ ] 냉장고 기반 추천 화면은 1~8개 결과를 보여야 합니다.
- [ ] 선택 재료가 적합하지 않을 때는 빈 결과와 안내 문구를 보여야 합니다.
- [ ] 추천 카드에서 저장 시 Home의 `Saved Recipes` 숫자가 증가해야 합니다.
- [ ] 상세 화면에서 저장 시 Home의 `Saved Recipes` 숫자가 증가해야 합니다.
- [ ] Recipe Detail에서 `Start Cooking` 후 Cook Mode가 자동 시작되어야 합니다.
- [ ] step 타이머가 0이 되면 다음 step으로 자동 이동해야 합니다.
- [ ] 총 40초 레시피는 step 합계 기준으로 40초 안에 완료되어야 합니다.
- [ ] 마지막 step 완료 시 `cooking_sessions`가 1건 증가해야 합니다.
- [ ] 마지막 step 완료 시 Home의 `Completed Recipes` 숫자가 증가해야 합니다.
- [ ] Home / Recommendation / Detail 경로가 fallback-first로 동작하는지 확인해야 합니다.
- [ ] 기본 테스트 세트는 빠르게 끝나야 합니다.

## 10. 이전 문서에서 이어받는 백로그

### 10.1 운영/신뢰성

- [ ] rate limit 대응
- [ ] timeout 대응
- [ ] OpenRouter 호출 실패 재시도 정책 고도화
- [ ] 운영 로그 및 호출 로그
- [ ] JSON Schema 응답 실패 시 사용자 수정 UX

### 10.2 추천/검색

- [ ] 2개 이하 재료 조합 검색
- [ ] 추천 결과 랭킹 고도화
- [ ] 추천 품질 개선용 랭킹/가중치 재설계
- [ ] 6개 조합 재검색에서도 결과가 너무 많을 때의 최종 제한 정책
- [ ] 기능별 모델 다변화
- [ ] Home 랜덤 추천의 샘플링 품질/편향 점검

### 10.3 데이터/정제

- [ ] 외부 레시피 정제 기준 고도화
- [ ] 내부 레시피 DB 품질 검수
- [ ] 단위가 다른 재료의 수량 변환 규칙
- [ ] recipe seed 적재 전략 추가 최적화
- [ ] 대용량 seed 적재 후 인덱스/통계 재생성 자동화

### 10.4 UX/화면

- [ ] Home에 최근 완료 카드 4개를 다시 넣을지 결정
- [ ] shopping list를 별도 화면으로 분리할지 결정
- [ ] 자연어 입력 후 저장 전 confirm 단계 추가 여부 결정
- [ ] `Complete Now` 버튼 유지 여부 결정
- [ ] 자동 완료 직전 사용자 확인 단계 여부 결정
- [ ] Fridge 텍스트 레이아웃 카테고리 기반 고도화
- [ ] 저장한 레시피 목록을 별도 화면으로 분리할지 결정

### 10.5 조리 세션

- [ ] Pause/Resume 상태를 새로고침 이후에도 복구할지 결정
- [ ] Stop 이후 재진입 시 항상 1단계부터 시작할지, 중단 step부터 재개할지 결정
- [ ] 부분 조리 세션 복구

### 10.6 장기 기능

- [ ] 사진 기반 추천
- [ ] 주간 식단
- [ ] 주간 장보기 최적화
- [ ] 개인화 추천
- [ ] 소셜 기능

## 11. 가정

- [ ] Home 추천은 탐색용 랜덤 레시피 노출이며, 개인화나 냉장고 최적화 목적이 아닙니다.
- [ ] 냉장고 기반 추천은 별도 화면으로 분리함으로써, Home은 가볍고 빠른 진입 화면으로 유지합니다.
- [ ] 냉장고 기반 추천은 사용자가 직접 선택한 재료를 최우선 입력으로 사용합니다.
- [ ] Cook Mode의 전체 시간은 별도 상수가 아니라 step 시간 합계로 계산합니다.
- [ ] 빠른 피드백을 위해 UI 경로는 정확도보다 응답 속도를 우선하며, 고비용 LLM 경로는 기본값에서 제외합니다.
- [ ] 사용자의 피드백은 1차적으로 `저장(별표)`과 `완료` 두 신호만 수집합니다.
