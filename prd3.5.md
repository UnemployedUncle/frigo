# 요리 여정 PRD v3.5

## 1. 문서 목적

이 문서는 현재 구현된 Frigo를 더 빠르고 가볍게 유지하기 위한 보수적 리팩토링 실행 문서입니다.

이번 버전은 기능 확장 PRD가 아닙니다.

- 사용자에게 보이는 핵심 플로우는 유지합니다.
- 내부 경로를 단순화합니다.
- 불필요한 코드와 deprecated 경계를 줄입니다.
- 대용량 데이터 기준의 체감 속도를 더 안정적으로 유지합니다.

기준 문서:

- [prd3.md](./prd3.md)
- [current-development-summary.md](./current-development-summary.md)
- [README.md](./README.md)

## 2. 이번 버전 목표

이번 정리 단계의 목표는 아래 4가지입니다.

- UI 핵심 경로에서 불필요한 LLM/agent 의존을 더 줄입니다.
- dead code, stale route, 미사용 경로를 정리합니다.
- DB 조회, 정책 계산, 화면 렌더 책임을 더 분리합니다.
- 기본 테스트 경로를 빠르게 유지하고 smoke 경로를 분리합니다.

유지해야 하는 사용자 경험:

1. Home은 즉시 열리고 무작위 레시피 8개를 보여줘야 합니다.
2. Fridge는 자연어 입력, 수정, 추천 선택이 빠르게 동작해야 합니다.
3. Recipe Detail은 fallback-safe shopping 계산으로 즉시 읽혀야 합니다.
4. Cook Mode는 브라우저 상태 중심으로 step이 자동 진행되어야 합니다.

## 3. 현재 문제 진단

현재 코드 기준으로 정리 대상은 아래와 같습니다.

### 3.1 문서와 실제 구현의 불일치

- README가 오래된 기준 문서와 없는 파일을 참조하고 있었습니다.
- 레거시 경로와 현재 경로가 한 문서 안에서 명확히 분리되지 않았습니다.

### 3.2 route와 서비스 책임 혼합

- [app/main.py](./app/main.py)에 화면 조합 로직과 정책 로직이 함께 존재합니다.
- 선택 재료 로드, 검증, 추천 렌더 전환이 route helper 수준에 섞여 있습니다.

### 3.3 추천 경로의 책임 경계 불명확

- `RecipeService.recommend_from_selected_items()`는 별도 책임 이름을 갖고 있지만 내부적으로 일반 추천 경로를 우회 호출하는 구조입니다.
- UI 선택 재료 추천과 agent 기반 추천의 경계가 코드에서 더 분명해질 필요가 있습니다.

### 3.4 UI 주 경로와 무관한 부수 경로 잔존

- `recipe_search_plans` persistence는 현재 핵심 UI 경험이 아닙니다.
- `POST /ui/recommend`는 실질적으로 현재 플로우에서 의미가 약한 경로입니다.
- `CookingService.recent_completed()`는 현재 Home 렌더 경로에서 사용되지 않습니다.

### 3.5 deprecated 필드와 레거시 경계 노출

- `workflow_file`이 recipe schema와 seed 경로에 계속 남아 있습니다.
- `estimated_minutes`가 workflow schema, migration, seed 경로에 남아 있습니다.
- `data/workflows`는 더 이상 runtime source가 아니지만 문맥상 레거시 흔적이 남아 있습니다.

### 3.6 단순 경로의 비효율

- 냉장고 입력 insert는 row-by-row execute 구조입니다.
- 선택 재료 추천 경로는 UI 전용 경로지만 서비스 구조상 별도 entrypoint 의도가 충분히 드러나지 않습니다.
- 테스트와 문서가 cleanup 후보를 현재 코드 기준으로 충분히 분리해 보여주지 못합니다.

## 4. 리팩토링 원칙

이번 버전은 아래 원칙을 고정합니다.

- `fallback-first`를 유지합니다.
- 사용자 플로우, route URL, DB schema 호환성을 우선합니다.
- 삭제 가능한 코드부터 제거하고, 그 다음에 책임 경계를 정리합니다.
- 성능 개선은 대용량 DB safe query 경로를 우선합니다.
- UI 핵심 경로에서는 저장이 꼭 필요하지 않은 부수효과를 줄입니다.
- deprecated 필드는 즉시 삭제보다 `주 경로 비노출`을 우선합니다.

## 5. 실행 항목

### 5.1 Route / Service 책임 정리

- `main.py`는 request parsing, redirect, template composition 중심으로 유지합니다.
- 선택 재료 추천용 서비스 entrypoint를 명확한 전용 경로로 둡니다.
- 냉장고 선택 검증, 추천 호출, 화면 렌더 사이의 책임을 더 분명히 나눕니다.
- `ShoppingService`는 계산과 저장 분리를 유지하고, Recipe Detail 경로는 계산 전용 사용을 고정합니다.

### 5.2 Dead Code 제거

- `POST /ui/recommend` 제거 여부를 우선 검토하고, 참조가 없으면 제거합니다.
- 현재 UI 핵심 흐름에서 사용되지 않는 메서드와 helper를 정리합니다.
- stale docs와 stale tests는 현재 구조에 맞게 정리합니다.

정리 우선 후보:

- `POST /ui/recommend`
- `CookingService.recent_completed()`
- 현재 더 이상 기준이 아닌 문서 내 오래된 route 또는 field 설명

### 5.3 Deprecated 경계 축소

- `workflow_file`, `estimated_minutes`를 runtime 주 경로에서 완전히 비주요화합니다.
- README, PRD, 테스트, schema 문서에서 deprecated 표현을 통일합니다.
- runtime source of truth는 계속 `workflow_steps.estimated_seconds`로 고정합니다.
- `data/workflows`는 archive/legacy 문맥에서만 다룹니다.

### 5.4 성능 개선

- random recipe query 경로는 large-table-safe 방식 유지 여부를 검증합니다.
- 냉장고 insert/update query는 batch 또는 단순화 가능한 경로를 검토합니다.
- selected-item recommendation은 plan persistence 없이 동작하는 UI 전용 경로라는 점을 더 분명히 합니다.
- workflow/detail 렌더 경로의 중복 계산과 불필요한 DB round-trip이 있는지 점검합니다.

### 5.5 테스트 정리

- route 테스트는 현재 UI 핵심 흐름 기준으로 유지합니다.
- service 테스트는 추천 책임 분리 이후의 entrypoint를 기준으로 갱신합니다.
- 기본 테스트와 large-seed smoke 테스트의 구분을 유지합니다.
- deprecated 경계 축소 후에도 fallback 경로가 깨지지 않는지 확인합니다.

## 6. 유지할 인터페이스와 호환성

이번 버전에서 유지할 UI 경로:

- `GET /`
- `GET /fridge`
- `GET /recommendations/fridge`
- `GET /recipes/{recipe_id}`
- `GET /cook/{recipe_id}`

유지할 action 경로:

- `POST /ui/fridge/parse`
- `POST /ui/fridge/items/{item_id}/update`
- `POST /ui/fridge/items/{item_id}/delete`
- `POST /recommendations/fridge`
- `POST /recipes/{recipe_id}/save`
- `POST /cook/{recipe_id}/complete`

정리 후보로 명시할 내부/비핵심 경로:

- `POST /ui/recommend`
- `recipe_search_plans` persistence path

고정 데이터 규칙:

- workflow runtime source of truth는 `workflow_steps.estimated_seconds`
- Home, Fridge, Recipe Detail, Cook Mode의 사용자-visible 동작은 유지

## 7. 완료 기준

아래 조건을 만족하면 이번 리팩토링 정리는 완료입니다.

- Home, Fridge, Recipe Detail, Cook Mode의 사용자-visible 동작 변화가 없습니다.
- UI 핵심 경로에서 OpenRouter 실패 시에도 정상 동작합니다.
- deprecated/legacy 관련 문서와 코드 참조가 일관됩니다.
- 기본 테스트는 빠르게 통과하고, large-seed smoke는 선택 실행으로 유지됩니다.
- cleanup 후보가 문서와 코드에서 같은 기준으로 관리됩니다.

## 8. 검증 기준

구현 후 확인 항목:

- README 링크가 현재 존재하는 파일만 가리키는지 확인
- README와 실제 구현 라우트/기능 목록이 일치하는지 확인
- `prd3.5.md`의 정리 항목이 현재 코드에서 실제 근거를 갖는지 확인
- deprecated 항목과 레거시 항목이 과장 없이 실제 코드 기준인지 확인
- 기본 테스트가 cleanup 이후에도 빠르게 유지되는지 확인

## 9. 이번 버전에서 하지 않는 것

이번 정리 단계에서 아래 항목은 하지 않습니다.

- 새로운 사용자 기능 추가
- 사진 입력/추천 도입
- DB schema 대규모 재설계
- route URL 전면 변경
- Cook Mode 세션 복구 추가
- 추천 엔진 전체 교체

## 10. 구현 체크리스트

- [ ] README를 현재 구현 기준으로 정리합니다.
- [ ] route와 service 책임 정리 대상을 확정합니다.
- [ ] dead code 제거 후보를 확인하고 우선순위를 정합니다.
- [ ] deprecated 필드를 주 경로에서 더 멀리 밀어냅니다.
- [ ] selected-item recommendation 경계를 더 명확히 정리합니다.
- [ ] fridge insert/update의 단순화 가능 경로를 점검합니다.
- [ ] 기본 테스트와 smoke 테스트 경계를 다시 검토합니다.
