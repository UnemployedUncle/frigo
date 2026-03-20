# 요리 여정 PRD v2

## 1. 문서 목적

이 문서는 현재 서비스의 다음 구현 단계를 `실행 가능한 text-first flow` 기준으로 고정하기 위한 문서입니다.

이번 단계의 핵심 목표는 아래와 같습니다.

- 사진 없이 텍스트만으로 전체 플로우를 구성합니다.
- 주간 식단은 제외합니다.
- `Home -> Fridge -> Recipe Detail -> Cook Mode -> Complete` 흐름이 실제로 동작해야 합니다.
- 사용자는 냉장고를 자연어로 입력하고, 추천 레시피를 보고, 장보기 목록을 확인한 뒤, 단계별 조리를 수행할 수 있어야 합니다.

기준 문서는 아래 3개입니다.

- 현재 코드베이스의 실제 구현 상태
- [Archive/260316_README.md](/Users/yongsupyi/Desktop/frigo/Archive/260316_README.md)
- [Archive/260317_textRepresentation.md](/Users/yongsupyi/Desktop/frigo/Archive/260317_textRepresentation.md)

현재 문서의 상태 표기 규칙은 아래와 같습니다.

- `[x]` 현재 코드 기준 구현 완료
- `[ ]` 아직 추가 개발 필요

## 2. 제품 목표

이번 버전은 `텍스트 기반 cooking tracker`입니다.

핵심 경험은 아래 4단계입니다.

1. Home에서 잔디와 추천 레시피를 확인합니다.
2. Fridge에서 자연어로 재료를 입력하고 실제 값을 수정합니다.
3. Recipe Detail에서 재료, shopping list, 전체 workflow를 확인합니다.
4. Cook Mode에서 타이머 기반으로 step을 자동 진행하고 완료 기록을 남깁니다.

## 3. 범위

### 3.1 포함 범위

- [x] Home은 `잔디 + 추천 레시피 8개`만 보여줍니다.
- [x] Fridge는 별도 `/fridge` 화면으로 제공합니다.
- [x] Fridge 화면에는 `자연어 입력 + 텍스트 냉장고 + 편집 테이블`을 모두 둡니다.
- [x] Recipe Detail은 `재료 + shopping list + 전체 workflow + Start Cooking`으로 구성합니다.
- [x] Cook Mode는 `자동 타이머 + 자동 다음 step 이동 + Pause / Resume / Stop`을 지원합니다.
- [x] 마지막 step 완료 시 `cooking_sessions`에 완료 기록을 저장합니다.
- [x] 100개 workflow 모두 `estimated_seconds`를 가져야 합니다.

### 3.2 제외 범위

- [ ] 사진 기반 추천
- [ ] 주간 식단
- [ ] 주간 장보기 최적화
- [ ] 부분 조리 세션 복구
- [ ] 개인화 추천
- [ ] 소셜 기능

## 4. 화면 구조

### 4.1 Home (`/`)

Home은 아래 두 블록만 가집니다.

- `Cooking Grass`
- `Recommended Recipes 8`

세부 요구사항:

- [x] 잔디는 날짜별 완료 레시피 수를 기준으로 표시합니다.
- [x] 추천 레시피는 최대 8개 노출합니다.
- [x] 각 추천 카드는 `제목`, `한 줄 설명`, `핵심 재료`, `View Recipe`를 보여줍니다.
- [x] Home에는 냉장고 입력, 냉장고 텍스트 블록, 편집 테이블, 최근 완료 카드를 두지 않습니다.

### 4.2 Fridge (`/fridge`)

Fridge는 냉장고 운영 화면입니다.

상단:

- [x] 자연어 입력 textarea
- [x] 입력 안내 문구
- [x] 저장 직후 `parsed preview` 텍스트 목록

중단:

- [x] 텍스트 냉장고 블록
- [x] `DOOR / FRIDGE / FRIDGE2 / DOOR2 / FREEZER` 구조 유지
- [x] 각 항목은 `이름 + 수량/단위 + D-day/상태`를 텍스트로 표시

하단:

- [x] 실제 값 편집 테이블
- [x] 컬럼은 `name / quantity / unit / expiry_date / save / delete`

### 4.3 Recipe Detail (`/recipes/{recipe_id}`)

Recipe Detail은 실행 전 검토 화면입니다.

- [x] `required_ingredients` 전체를 텍스트로 표시합니다.
- [x] 현재 냉장고 기준 shopping list를 같은 화면에서 보여줍니다.
- [x] 전체 workflow step을 모두 보여줍니다.
- [x] 각 step은 `번호 / 제목 / 설명 / 도구 / estimated_seconds`를 표시합니다.
- [x] `Start Cooking` 버튼으로 Cook Mode에 진입합니다.

### 4.4 Cook Mode (`/cook/{recipe_id}`)

Cook Mode는 실행 화면입니다.

- [x] 현재 step 1개를 크게 보여줍니다.
- [x] `estimated_seconds` 기반 카운트다운이 자동 시작됩니다.
- [x] 타이머가 0이 되면 자동으로 다음 step으로 이동합니다.
- [x] 마지막 step은 자동 완료 처리합니다.
- [x] 사용자 제어는 `Pause`, `Resume`, `Stop`, `Complete Now`를 제공합니다.
- [x] `Stop`은 미완료 상태로 종료하고 Recipe Detail로 돌아갑니다.

## 5. 데이터 및 인터페이스

### 5.1 라우트

- [x] `GET /` : Home
- [x] `GET /fridge` : Fridge 화면
- [x] `POST /ui/fridge/parse` : 자연어 입력 저장 후 preview 포함 렌더
- [x] `POST /ui/fridge/items/{item_id}/update` : 냉장고 항목 수정
- [x] `POST /ui/fridge/items/{item_id}/delete` : 냉장고 항목 삭제
- [x] `GET /recipes/{recipe_id}` : Recipe Detail
- [x] `GET /cook/{recipe_id}` : Cook Mode
- [x] `POST /cook/{recipe_id}/complete` : 완료 기록 저장

### 5.2 데이터 구조

완료 기록은 `cooking_sessions`를 사용합니다.

- [x] `id`
- [x] `recipe_id`
- [x] `completed_at`
- [x] `actual_seconds`
- [x] `created_at`

workflow step은 아래 필드를 기준으로 합니다.

- [x] `recipe_id`
- [x] `step_number`
- [x] `title`
- [x] `description`
- [x] `ingredients`
- [x] `tool`
- [x] `estimated_seconds`

규칙:

- [x] `estimated_seconds`는 1~10초 범위입니다.
- [x] `estimated_minutes`는 호환용 보조 필드로만 유지합니다.
- [x] Home 추천은 `fallback-safe` 경로로 최대 8개 반환합니다.
- [x] Recipe Detail의 shopping list는 현재 `fridge_items` 기준 실시간 계산 결과입니다.

### 5.3 Legacy / Transitional

- [x] runtime workflow source of truth는 `workflow_steps` 테이블입니다.
- [x] `workflow_file`는 호환용 보조 필드로만 유지합니다.
- [x] `estimated_minutes`는 deprecated 상태이며 `estimated_seconds`가 주 필드입니다.
- [x] UI 화면 경로는 LLM보다 fallback 로직을 우선 사용합니다.

## 6. 구현 체크리스트

### 6.1 Home

- [x] Home에서 냉장고 관련 UI를 제거합니다.
- [x] 잔디와 추천 레시피 8개만 남깁니다.

### 6.2 Fridge

- [x] `/fridge` 템플릿을 추가합니다.
- [x] 자연어 입력 결과 preview를 표시합니다.
- [x] 텍스트 냉장고와 편집 테이블을 같은 화면에서 제공합니다.

### 6.3 Recipe Detail

- [x] `/recipes/{recipe_id}` 화면을 기준 경로로 사용합니다.
- [x] 레시피 재료, shopping list, workflow를 한 화면에 묶습니다.

### 6.4 Cook Mode

- [x] 자동 카운트다운을 구현합니다.
- [x] 0초 도달 시 자동 다음 step 이동을 구현합니다.
- [x] 마지막 step에서는 자동 완료 처리합니다.
- [x] Pause / Resume / Stop UI를 제공합니다.
- [x] Stop 시 부분 진행 상태는 저장하지 않습니다.

### 6.5 데이터

- [x] 100개 workflow의 `estimated_seconds`를 검증합니다.
- [x] 완료 기록 seed를 유지합니다.

## 7. 예시 화면

### 7.1 Home

```text
Frigo Home

Cooking Grass
[날짜별 완료 수]

Recommended For Tonight
[Card] Chicken Divan
[Card] Egg Drop Soup
[Card] Sesame Ginger Chicken
...
```

### 7.2 Fridge

```text
Fridge

Natural Input
시금치 1봉지 내일, 새우 200g 오늘, 버터 1개

Parsed Preview
- 시금치 / 1 봉지 / 2026-03-18
- 새우 / 200 g / 2026-03-17

FRIGO
DOOR / FRIDGE / FRIDGE2 / DOOR2 / FREEZER

Edit Table
name | quantity | unit | expiry_date | save | delete
```

### 7.3 Recipe Detail

```text
Recipe Detail

Chicken Divan

Ingredients
- margarine 1/4 c.
- onion 1/4 c.

Shopping List
- broccoli / need 1 pkg / have 0 / missing

Full Workflow
1. Saute / pan / 7s
2. Heat / general / 6s
...

Start Cooking
```

### 7.4 Cook Mode

```text
Cooking Mode

Step 2 of 10
Heat
Time left: 06s

[Pause] [Resume] [Stop] [Complete Now]

0초 도달 -> 자동 다음 step 이동
마지막 step 종료 -> 자동 완료
```

## 8. 테스트 계획

- [x] `/`에서 잔디와 추천 8개만 보여야 합니다.
- [x] `/`에 냉장고 입력이나 편집 테이블이 없어야 합니다.
- [x] `/fridge`에서 자연어 입력, preview, 텍스트 냉장고, 편집 테이블이 모두 보여야 합니다.
- [x] 자연어 입력 후 결과가 preview와 저장 데이터에 동시에 반영되어야 합니다.
- [x] `/recipes/{recipe_id}`에서 재료, shopping list, workflow가 모두 보여야 합니다.
- [x] `/cook/{recipe_id}`에서 카운트다운이 자동 시작되어야 합니다.
- [x] 카운트다운 종료 시 다음 step으로 자동 이동해야 합니다.
- [x] `Pause`, `Resume`, `Stop`이 화면에 있어야 합니다.
- [x] 마지막 step 완료 시 `cooking_sessions`가 1건 증가해야 합니다.
- [x] workflow validator가 100개 파일을 통과해야 합니다.

## 9. 현재 구현 상태 요약

- [x] `docker compose up --build -d` 기준으로 migration, seed, workflow validation 후 앱이 기동됩니다.
- [x] Home은 잔디와 추천 8개만 보여줍니다.
- [x] Fridge는 별도 화면으로 분리되어 있습니다.
- [x] Recipe Detail은 shopping list와 workflow를 함께 보여줍니다.
- [x] Cook Mode는 자동 진행과 완료 기록 저장을 지원합니다.

## 10. 추가 개발 필요 사항

- [ ] Cook Mode의 pause/resume 상태를 브라우저 새로고침이나 이탈 후에도 복구할지 결정 후 구현이 필요합니다.
- [ ] `Stop` 이후 다시 조리를 시작할 때 이전 step부터 재개할지, 항상 1단계부터 시작할지 명확한 정책 구현이 필요합니다. 현재는 항상 상세 화면으로만 복귀합니다.
- [ ] Home 추천 품질을 더 높이기 위한 랭킹 개선이 필요합니다. 현재는 text-first 응답속도를 우선한 fallback-safe 추천입니다.
- [ ] Fridge 텍스트 레이아웃의 칸 배치 규칙을 재료 카테고리 기반으로 고도화할 여지가 있습니다. 현재는 단순 분배 + 일부 freezer 키워드 기반입니다.
- [ ] Recipe Detail의 shopping list를 저장 이력과 연결할지, 현재처럼 조회 시점 계산만 유지할지에 대한 후속 개발이 필요합니다.
- [ ] 시드 데이터 100건의 품질 검수와 레시피/재료 정규화 고도화가 추가로 필요합니다.

## 11. 결정 필요 사항

- [ ] Home에 최근 완료 카드 4개를 다시 넣을지 여부를 결정해야 합니다. 현재는 범위에서 제외했습니다.
- [ ] `Complete Now` 버튼을 유지할지, 마지막 step 자동 완료만 허용할지 결정이 필요합니다.
- [ ] shopping list를 별도 화면으로 분리할지, 현재처럼 Recipe Detail 내부 섹션으로 유지할지 결정이 필요합니다.
- [ ] Cook Mode의 타이머 만료 시 자동 완료 직전에 사용자 확인 단계를 둘지 여부를 결정해야 합니다.
- [ ] 자연어 입력 결과를 저장 전에 사용자가 수정할 수 있는 preview-confirm 단계가 필요한지 결정해야 합니다.

## 12. 백로그

- [ ] 사진 기반 추천
- [ ] 주간 식단
- [ ] 부분 조리 세션 복구
- [ ] 개인화 추천

## 13. 가정

- [ ] Home의 “레시피만”은 추천 레시피 8개를 의미합니다.
- [ ] 최근 완료 카드 4개는 이번 Home 범위에서 제외합니다.
- [ ] shopping list는 별도 독립 화면이 아니라 Recipe Detail 내부 섹션으로 제공합니다.
- [ ] Cook Mode의 자동 진행은 브라우저 내 상태로 처리합니다.
