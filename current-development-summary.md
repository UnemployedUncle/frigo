# Frigo Current Development Summary

기준일: 2026-03-20

## 1. 문서 목적

이 문서는 현재까지 구현된 Frigo의 상태를 한 문서로 정리한 기준 문서입니다.

- 실제 코드 기준의 현재 동작 범위를 빠르게 파악할 수 있어야 합니다.
- UX/UI 설계, 기획 정리, 이후 PRD 업데이트의 공통 참고 문서로 사용합니다.
- 기획 의도와 실제 구현 상태가 다른 지점은 별도로 표시합니다.

기준으로 확인한 문서와 코드:

- [README.md](/Users/yongsupyi/Desktop/frigo/README.md)
- [prd3.md](/Users/yongsupyi/Desktop/frigo/prd3.md)
- [Archive/prd.md](/Users/yongsupyi/Desktop/frigo/Archive/prd.md)
- [Archive/prd2.md](/Users/yongsupyi/Desktop/frigo/Archive/prd2.md)
- [app/main.py](/Users/yongsupyi/Desktop/frigo/app/main.py)
- [app/templates/index.html](/Users/yongsupyi/Desktop/frigo/app/templates/index.html)
- [app/templates/fridge.html](/Users/yongsupyi/Desktop/frigo/app/templates/fridge.html)
- [app/templates/recommendations.html](/Users/yongsupyi/Desktop/frigo/app/templates/recommendations.html)
- [app/templates/recipe_detail.html](/Users/yongsupyi/Desktop/frigo/app/templates/recipe_detail.html)
- [app/templates/workflow.html](/Users/yongsupyi/Desktop/frigo/app/templates/workflow.html)

## 2. 제품 한 줄 정의

Frigo는 냉장고 재료를 텍스트로 입력하고, 현재 재고를 기반으로 레시피를 탐색한 뒤, 장보기 목록과 단계별 타이머를 보며 조리 완료까지 기록하는 text-first cooking tracker입니다.

## 3. 현재 구현 범위

현재 사용 가능한 핵심 흐름:

1. Home에서 최근 완료 잔디, 저장 수, 완료 수, 무작위 레시피 8개를 확인합니다.
2. Fridge에서 자연어로 재료를 입력하고 저장합니다.
3. Fridge에서 현재 재료를 텍스트 냉장고와 편집 테이블로 관리합니다.
4. Fridge에서 재료를 선택해 냉장고 기반 추천 화면으로 이동합니다.
5. Recipe Detail에서 재료, 쇼핑 리스트, 전체 workflow를 확인합니다.
6. Cook Mode에서 단계별 타이머를 자동 진행하고 완료 기록을 남깁니다.
7. 레시피를 저장하거나 저장 해제할 수 있습니다.

현재 명시적으로 제외되거나 미구현인 범위:

- 사진 기반 입력 및 추천
- 주간 식단 계획
- 고급 개인화 추천
- 부분 조리 세션 복구
- 장기 세션 저장/재개

## 4. 정보 구조와 화면 목록

### 4.1 Home (`/`)

목적:

- 서비스 진입점
- 저장/완료 현황 확인
- 랜덤 레시피 탐색 시작

현재 표시 요소:

- Hero 문구
- `Saved Recipes` 수
- `Completed Recipes` 수
- 최근 14일 기준 `Cooking Grass`
- 무작위 추천 레시피 최대 8개

각 레시피 카드 요소:

- 제목
- 요약
- 핵심 재료 최대 3개
- `View Recipe`
- `Save` 또는 `Unsave`

현재 구현 특징:

- Home은 냉장고 기반 추천이 아니라 무작위 추천만 사용합니다.
- 저장 상태는 카드 단위로 즉시 토글됩니다.
- Home에서 바로 냉장고 입력은 하지 않습니다.

### 4.2 Fridge (`/fridge`)

목적:

- 냉장고 입력
- 현재 보유 재료 확인
- 재료 수정/삭제
- 추천용 재료 선택

현재 표시 요소:

- 자연어 입력 폼
- 입력 예시 문구
- 저장 직후 `Parsed Preview`
- ASCII 스타일 `Text Fridge`
- 냉장고 구획: `DOOR / FRIDGE / FRIDGE2 / DOOR2 / FREEZER`
- 추천용 재료 선택 체크박스 목록
- 실제 값 편집 테이블

편집 가능한 값:

- 이름
- 수량
- 단위
- 유통기한

현재 구현 특징:

- 자연어 입력 결과는 저장 후 즉시 preview로 다시 보여줍니다.
- 냉장고 레이아웃은 실제 위치 기반이 아니라 규칙 기반 텍스트 표현입니다.
- 추천 선택 UI는 체크박스 기반입니다.
- 선택 개수의 실시간 카운터는 아직 없습니다.

### 4.3 Fridge Recommendations (`/recommendations/fridge`)

목적:

- 사용자가 직접 고른 냉장고 재료 기준 추천 결과 확인

현재 표시 요소:

- 선택한 재료 pill 목록
- 추천 레시피 카드 최대 8개
- `Back To Fridge`
- `Home`

각 카드 요소:

- 제목
- 요약
- 핵심 재료 최대 3개
- `View Recipe`
- `Save` 또는 `Unsave`

현재 구현 특징:

- 선택 재료는 사용자가 고른 항목을 그대로 사용합니다.
- 추천 결과가 없으면 빈 상태 문구를 표시합니다.

### 4.4 Recipe Detail (`/recipes/{recipe_id}`)

목적:

- 조리 시작 전 검토 화면

현재 표시 요소:

- 레시피 제목, 요약
- `Home`, `Fridge`, `Save`, `Start Cooking`
- 전체 재료 목록
- cuisine, servings, total timer
- primary ingredient pills
- shopping list
- 전체 workflow step 목록

workflow 표시 정보:

- step 번호
- step 제목
- 설명
- 도구
- `estimated_seconds`

현재 구현 특징:

- shopping list는 현재 냉장고 상태 기준으로 즉시 계산합니다.
- 상세 화면에서도 저장 토글이 가능합니다.

### 4.5 Cook Mode (`/cook/{recipe_id}`)

목적:

- 현재 단계 중심의 조리 실행 화면

현재 표시 요소:

- 현재 step 번호
- 현재 step 제목/설명
- 현재 step timer
- 전체 남은 시간
- tool
- ingredient pills
- 전체 workflow 목록
- `Pause`
- `Resume`
- `Stop`
- `Complete Now`

현재 구현 특징:

- 첫 진입 시 자동 시작됩니다.
- step 타이머가 0이 되면 자동으로 다음 step으로 넘어갑니다.
- 마지막 step이 끝나면 자동으로 완료 요청을 보냅니다.
- `Stop`은 상세 화면으로 돌아가며 완료 기록을 남기지 않습니다.
- timer 진행은 브라우저 스크립트에서 처리합니다.

## 5. 주요 사용자 액션

현재 UI에서 가능한 주요 액션:

- 냉장고 자연어 입력 저장
- 냉장고 항목 수정
- 냉장고 항목 삭제
- 추천용 재료 선택 후 추천 실행
- 레시피 저장/해제
- 레시피 상세 진입
- Cook Mode 진입
- 조리 일시정지/재개/중단/즉시완료

## 6. 핵심 동작 규칙

### 6.1 냉장고 입력

- OpenRouter가 가능하면 구조화 파싱을 시도합니다.
- LLM 응답이 비정상적이면 로컬 fallback 파서로 처리합니다.
- `오늘`, `내일`, `모레`, `이번 주말`, `다음 주 화요일`, `3월 18일` 같은 표현을 해석합니다.
- 파싱된 재료는 입력 로그와 함께 저장됩니다.

### 6.2 냉장고 기반 추천

- 냉장고에 저장된 재료가 없으면 추천 화면으로 갈 수 없습니다.
- 저장 재료가 5개 미만이면 전체 재료를 자동 사용합니다.
- 저장 재료가 5개 이상이면 정확히 5개를 골라야 합니다.
- 잘못 고르면 Fridge 화면으로 돌아오고 에러 문구를 보여줍니다.
- 추천 결과는 최대 8개까지 표시합니다.

### 6.3 쇼핑 리스트

- 레시피의 `required_ingredients`를 기준으로 계산합니다.
- 냉장고에 없는 재료는 `missing`
- 절반 이하로 부족하면 `half_or_less`
- 일부 부족하면 `insufficient`
- 충분하면 리스트에서 제외합니다.

### 6.4 저장/완료

- 저장과 완료는 서로 독립입니다.
- 저장은 토글형 단일 상태입니다.
- 완료는 누적 기록입니다.
- Home은 저장 수와 완료 수를 따로 표시합니다.

### 6.5 Cook Mode

- 전체 시간은 모든 step의 `estimated_seconds` 합입니다.
- `Pause`는 브라우저 내 카운트다운만 멈춥니다.
- `Resume`은 같은 페이지 상태에서 이어집니다.
- `Complete Now`는 즉시 완료 기록을 남깁니다.

## 7. 데이터와 상태

현재 UX에 직접 영향을 주는 데이터 단위:

- `fridge_items`: 현재 냉장고 재고
- `recipes`: 레시피 메타데이터
- `workflow_steps`: step별 조리 흐름
- `saved_recipes`: 저장 상태
- `cooking_sessions`: 완료 기록
- `recipe_search_terms`: 추천 검색 인덱스

화면에서 직접 사용하는 상태:

- 저장 여부
- 완료 수
- 최근 14일 완료 분포
- 선택한 냉장고 재료 목록
- shopping list 비어 있음/존재함
- cook 진행 중 / pause / 완료

## 8. 라우트 요약

주요 UI 라우트:

- `GET /`
- `GET /fridge`
- `POST /ui/fridge/parse`
- `POST /ui/fridge/items/{item_id}/update`
- `POST /ui/fridge/items/{item_id}/delete`
- `POST /recommendations/fridge`
- `GET /recommendations/fridge`
- `GET /recipes/{recipe_id}`
- `POST /recipes/{recipe_id}/save`
- `GET /cook/{recipe_id}`
- `POST /cook/{recipe_id}/complete`

병행 유지 중인 API 성격 라우트:

- `POST /fridge/parse`
- `GET /fridge/items`
- `PATCH /fridge/items/{item_id}`
- `DELETE /fridge/items/{item_id}`
- `POST /recipes/recommend`
- `POST /shopping-list`
- `GET /recipes/{recipe_id}/workflow`

## 9. 현재 디자인에 영향을 주는 제약

- 제품 방향은 `text-first`입니다.
- Home, Recommendation, Recipe Detail은 기본적으로 LLM 없이도 동작해야 합니다.
- 조리 진행의 핵심 상태는 브라우저에 있습니다.
- Fridge와 Save 액션은 전통적인 form submit + redirect 흐름입니다.
- 모바일에서도 한 화면씩 읽히는 구조가 필요합니다.
- 대용량 recipe/workflow 데이터셋을 전제로 하므로 탐색 진입은 가벼워야 합니다.

## 10. 현재 구현과 PRD 사이의 차이

UX 설계 시 아래 차이를 인지해야 합니다.

- PRD에는 Fridge 선택 개수 표시가 있으나 현재 UI에는 실시간 카운터가 없습니다.
- PRD는 추천 결과 1~8개를 목표로 하지만 실제 결과 수는 데이터와 검색 조건에 따라 달라집니다.
- PRD는 선택 오류를 더 명확히 다룰 수 있게 열어두고 있지만 현재 `GET /recommendations/fridge`의 잘못된 접근은 조용히 `/fridge`로 리다이렉트됩니다.
- 현재 디자인은 텍스트 중심 프로토타입 스타일이며, 최종 UX 비주얼 시스템은 아직 고도화되지 않았습니다.

## 11. UX 설계용 연결 문서

이 문서를 바탕으로 실제 디자인 입력값을 정리한 문서는 아래입니다.

- [ux-design-reference.md](/Users/yongsupyi/Desktop/frigo/ux-design-reference.md)
