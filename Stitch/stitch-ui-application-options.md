# Stitch UI 적용 방안 문서

기준일: 2026-03-21

## 1. 문서 목적

이 문서는 `Stitch` HTML 시안을 참고해 현재 Frigo UI를 어떤 방식으로 변경할 수 있는지 비교하고, 가장 현실적인 적용 방안을 추천하기 위한 의사결정 문서입니다.

- 대상 화면: `Home`, `Fridge Management`, `Recommendation`, `Recipe Detail`, `Cook Mode`
- 목표: 현재 FastAPI + Jinja 구조와 핵심 동작은 유지하면서, 정보 구조와 시각 체계를 `Stitch` 수준으로 재정렬
- 범위: 전면 재구성 관점으로 검토하되, 백엔드 서비스 로직과 DB 스키마 변경은 제외

## 2. 기준 소스

이 문서는 아래 구현과 시안을 함께 기준으로 삼습니다.

- 현재 구현
  - `app/templates/base.html`
  - `app/templates/index.html`
  - `app/templates/fridge.html`
  - `app/templates/recommendations.html`
  - `app/templates/recipe_detail.html`
  - `app/templates/workflow.html`
  - `app/main.py`
- 현재 제품/UX 기준
  - `current-development-summary.md`
  - `Stitch/ux-design-reference.md`
- Stitch 시안
  - `Stitch/stitch_frigo_v1/frigo_home_unified/code.html`
  - `Stitch/stitch_frigo_v1/fridge_management_unified/code.html`
  - `Stitch/stitch_frigo_v1/fridge_recommendations_unified/code.html`
  - `Stitch/stitch_frigo_v1/recipe_detail_unified_refined/code.html`
  - `Stitch/stitch_frigo_v1/cook_mode_unified/code.html`

## 3. 현재 구조와 전환 전제

현재 Frigo는 이미 `text-first`, `server-rendered`, `fallback-first` 구조를 가지고 있습니다. 따라서 이번 UI 개편은 프론트엔드 스택 교체보다 아래 전제를 지키는 방식이 적합합니다.

- 유지 대상 라우트
  - `/`
  - `/fridge`
  - `/recommendations/fridge`
  - `/recipes/{recipe_id}`
  - `/cook/{recipe_id}`
- 유지 대상 사용자-visible 동작
  - Home의 랜덤 8개 추천
  - Fridge의 자연어 입력, parsed preview, 편집, 추천용 선택
  - Recommendation의 선택 재료 기반 결과
  - Recipe Detail의 shopping list와 workflow 미리보기
  - Cook Mode의 브라우저 타이머, 자동 step 전환, pause/resume/stop/complete
- 유지 대상 템플릿 컨텍스트 계약
  - 기본 권장안에서는 현재 `app/main.py`가 넘기는 데이터 구조를 바꾸지 않음

핵심 판단:

- `Stitch`는 시각/구조 참조로 활용
- Tailwind CDN HTML을 그대로 복붙하는 방식은 비권장
- 현재 Jinja 템플릿에 맞는 공통 CSS 토큰과 반복 컴포넌트로 번역하는 방식이 적합

## 4. 적용 방안 비교

### 방안 A. 직접 이식형

정의:

- 화면별 `Stitch` HTML을 거의 그대로 Jinja 템플릿으로 옮기고, 서버 데이터 바인딩만 삽입

장점:

- 시안과 가장 빠르게 비슷한 결과를 낼 수 있음
- 화면 단위 결과물이 명확해 디자이너 검수에 유리함
- 단기 데모나 내부 프레젠테이션 용도로는 속도가 빠름

단점:

- `base.html`과 각 화면 템플릿에 중복 구조가 많이 생김
- Tailwind CDN 구조를 현재 CSS 체계와 혼용하게 될 가능성이 큼
- 공통 내비게이션, 버튼, 패널, 카드, 상태 UI를 재사용하기 어려움
- Cook Mode처럼 동적 로직이 큰 화면은 마크업 이식 후 다시 손볼 부분이 많음

리스크:

- 화면 간 시각 일관성보다 시안 복제에 치우칠 수 있음
- 반응형 수정, 접근성 보정, 서버 데이터 조건 분기 처리 비용이 커짐

적합한 상황:

- 아주 빠르게 비주얼 샘플을 맞춰야 할 때
- 이후 재구축을 전제로 한 임시 전환일 때

### 방안 B. 디자인 시스템 이식형

정의:

- 먼저 공통 셸, 디자인 토큰, 카드/패널/액션 바/배지/테이블/타이머 컴포넌트를 만들고, 이후 각 화면을 새 구조로 재구성

장점:

- 장기적으로 가장 일관되고 유지보수성이 높음
- `base.html` 중심 구조 정리가 쉬움
- Home, Fridge, Recommendation, Detail, Cook 전체에서 동일한 시각 언어를 강하게 유지할 수 있음

단점:

- 선행 설계량이 큼
- 문서화 없이 바로 구현하면 공통화 범위가 과도해질 수 있음
- 현재 MVP 단계에서는 초기 작업량이 상대적으로 큼

리스크:

- 처음부터 너무 많은 컴포넌트를 추상화하면 작업 속도가 느려짐
- 실제 화면 요구보다 시스템 설계가 앞서는 문제가 생길 수 있음

적합한 상황:

- 이후 UI 반복 개발이 많을 때
- 장기 운영을 전제로 안정적인 기준 시스템이 필요할 때

### 방안 C. 하이브리드 단계적 전환형

정의:

- 공통 셸과 핵심 토큰만 먼저 도입하고, 각 화면은 우선순위에 따라 순차적으로 `Stitch` 구조를 번역해 교체

장점:

- 현재 구조와 가장 잘 맞음
- 라우트와 데이터 바인딩을 유지하면서 정보 위계와 레이아웃을 크게 개선할 수 있음
- `base.html` 재구성, 공통 CSS 정리, 반복 블록 부분화 같은 기반 작업과 화면 전환을 함께 진행할 수 있음
- Home, Recipe Detail, Cook Mode처럼 사용자 체감이 큰 화면부터 개편 가능

단점:

- 전환 중간에는 일부 화면만 새 스타일을 쓰는 과도기가 생길 수 있음
- 문서 없이 진행하면 화면 간 완성도 차이가 생길 수 있음

리스크:

- 우선순위와 공통 규칙이 명확하지 않으면 절충안이 누더기처럼 보일 수 있음

적합한 상황:

- 현재 Frigo와 가장 잘 맞는 방식
- 서버 렌더 기반을 유지하면서도 전면 재구성을 현실적으로 달성해야 할 때

## 5. 추천안

권장안은 `방안 C. 하이브리드 단계적 전환형`입니다.

추천 이유:

- 현재 라우트, 서비스, 템플릿 컨텍스트 계약을 유지할 수 있습니다.
- `Stitch` 시안의 강점인 정보 위계, 내비게이션, CTA 구조, 상태 배지를 흡수하면서도 구현 리스크를 नियंत्र할 수 있습니다.
- `base.html`을 먼저 재구성한 뒤 화면별로 전환하면 중복 없이 일관된 스타일을 축적할 수 있습니다.
- Cook Mode처럼 동적 로직이 이미 있는 화면도 UI만 안전하게 재배치할 수 있습니다.

권장 구현 원칙:

- `base.html`에서 공통 셸, 여백 체계, 타이포, 색상 토큰, 버튼 계열을 재정의
- 화면별 템플릿은 현재 데이터 바인딩을 유지한 채 마크업 구조만 재정렬
- 반복 UI는 partial 또는 Jinja macro 후보로 분리
- `Stitch`의 Tailwind CDN 코드는 그대로 쓰지 않고 현재 서버 렌더링 구조에 맞는 CSS 클래스로 번역
- 외부 API, 서비스 인터페이스, DB 스키마는 변경하지 않음

## 6. 화면별 적용 방향

아래 항목은 모든 화면에 같은 틀로 정리합니다.

- 현재 UI 구조
- Stitch 시안의 목표 구조
- 그대로 유지해야 하는 현재 동작
- 바뀌어야 하는 정보 위계와 상호작용
- 구현 난이도와 리스크

### 6.1 Home

현재 UI 구조:

- Hero + `Open Fridge` + 추천 섹션 이동 버튼
- 저장 수 / 완료 수 요약
- Cooking Grass
- 랜덤 추천 레시피 카드

Stitch 시안의 목표 구조:

- 좌측 고정 내비게이션 + 메인 대시보드
- 숫자 요약을 더 크게 노출
- 활동 로그와 추천 섹션을 명확히 분리
- 카드 스캔성을 높인 editorial형 구성

그대로 유지해야 하는 현재 동작:

- Home은 랜덤 8개 레시피를 보여줘야 함
- 저장 상태 토글이 카드 단위로 동작해야 함
- `Saved Recipes`, `Completed Recipes`, `Cooking Grass` 데이터는 그대로 유지

바뀌어야 하는 정보 위계와 상호작용:

- 첫 CTA를 `Open Fridge` 중심으로 더 명확히 배치
- 저장/완료 숫자를 카드형 요약이 아니라 대시보드 핵심 수치로 승격
- Grass는 보조 정보로 후순위 배치
- 추천 카드는 메타 정보와 액션 분리를 더 명확히 설계

구현 난이도와 리스크:

- 난이도: 중간
- 리스크: 좌측 고정 내비게이션을 도입할 경우 전체 공통 레이아웃 변경이 선행되어야 함

### 6.2 Fridge Management

현재 UI 구조:

- 자연어 입력
- parsed preview
- ASCII fridge
- 추천용 선택 카드
- 편집 테이블

Stitch 시안의 목표 구조:

- 입력 영역과 현재 자산 목록을 강하게 분리
- 선택 상태와 편집 액션을 테이블 중심으로 통합
- 하단 고정 액션 바 또는 선택 개수 중심 CTA 사용

그대로 유지해야 하는 현재 동작:

- 자연어 입력 저장
- parsed preview 표시
- 항목 수정/삭제
- 5개 선택 규칙 기반 추천 진입

바뀌어야 하는 정보 위계와 상호작용:

- `입력`, `미리보기`, `보유 목록`, `추천 선택`의 4영역을 더 명확히 분리
- 추천 선택 상태를 실시간 카운터와 함께 노출
- ASCII fridge는 시각 보조 영역으로 낮추고, 실제 관리 중심은 테이블 또는 리스트로 이동
- 추천 CTA는 선택 상태에 따라 더 직접적으로 보이게 조정

구현 난이도와 리스크:

- 난이도: 높음
- 리스크: 현재 한 화면에 기능 밀도가 높아서 레이아웃 재구성이 가장 큼

### 6.3 Recommendation

현재 UI 구조:

- 선택 재료 pill 목록
- 추천 카드 목록
- `Back To Fridge`, `Home`

Stitch 시안의 목표 구조:

- 선택 재료가 “추천 이유”처럼 보이는 헤더
- featured recommendation + secondary cards 구조
- 결과 없을 때도 다음 액션이 분명한 empty state

그대로 유지해야 하는 현재 동작:

- 선택 재료 기반 추천 결과 유지
- 카드별 `View Recipe`, `Save/Unsave`
- 결과 없음 문구 유지

바뀌어야 하는 정보 위계와 상호작용:

- 선택 재료를 단순 pill 나열이 아니라 결과 컨텍스트로 승격
- 첫 번째 추천 결과를 대표 카드로 강조할지 검토
- 결과 없음 상태에서 `Back To Fridge` 또는 재선택 유도 강화

구현 난이도와 리스크:

- 난이도: 중간
- 리스크: featured card를 도입해도 실제 추천 품질이 이를 뒷받침하는지 검토 필요

### 6.4 Recipe Detail

현재 UI 구조:

- 상단 제목/요약/액션
- 재료 목록
- summary 메타
- shopping list
- 전체 workflow

Stitch 시안의 목표 구조:

- 큰 타이포의 헤더
- 핵심 메타데이터 묶음
- 재료와 shopping list의 강한 시각 분리
- `Start Cooking` 우선의 CTA 구조
- workflow를 읽기 쉬운 editorial step 구조로 정리

그대로 유지해야 하는 현재 동작:

- `Save/Unsave`
- `Start Cooking`
- shopping list의 fallback-safe 계산 결과
- 전체 workflow step 표시

바뀌어야 하는 정보 위계와 상호작용:

- `Start Cooking`을 최우선 CTA로 고정
- 재료 목록과 shopping list를 같은 레벨로 보여주지 않고 목적별로 분리
- 총 시간, 인분, cuisine 등을 헤더 메타로 끌어올림
- workflow는 예습용 읽기 구조에 맞게 스캔 순서 정리

구현 난이도와 리스크:

- 난이도: 중간
- 리스크: shopping list가 비어 있는 상태와 많은 상태 모두에서 레이아웃이 자연스러워야 함

### 6.5 Cook Mode

현재 UI 구조:

- 현재 step 정보
- step 타이머, total remaining
- workflow 목록
- `Pause`, `Resume`, `Stop`, `Complete Now`

Stitch 시안의 목표 구조:

- 현재 단계에 집중하는 대형 타이포 레이아웃
- 타이머를 가장 강하게 노출
- 액션 수를 줄여 보이게 만드는 집중형 하단 제어 영역

그대로 유지해야 하는 현재 동작:

- 자동 step 전환
- pause/resume
- stop
- complete
- 브라우저 내 상태 기반 타이머 진행

바뀌어야 하는 정보 위계와 상호작용:

- 현재 instruction을 가장 크게 표시
- 전체 workflow는 보조 패널 또는 축약형 progress로 이동
- `Stop`과 `Complete Now`의 위험도 차이를 색과 위치로 분리
- 모바일에서 타이머와 핵심 버튼이 항상 보이도록 구성

구현 난이도와 리스크:

- 난이도: 중간
- 리스크: UI 집중도를 높이면서 기존 스크립트와 DOM 연결을 안전하게 유지해야 함

## 7. 공통 구현 방향

### 7.1 공통 레이아웃

- `base.html`을 공통 앱 셸 중심으로 재구성
- 데스크톱에서는 좌측 고정 내비게이션 또는 상단+서브내비 구조 중 하나로 통일
- 모바일에서는 상단 바 + 하단 내비 또는 축약 헤더를 사용

권장 판단:

- 데스크톱: 좌측 고정 내비게이션
- 모바일: 상단 헤더 + 하단 핵심 내비게이션

### 7.2 공통 디자인 토큰

- 색상: `primary`, `surface`, `surface-variant`, `ink`, `muted`, `outline`, `danger`
- 타이포: 헤드라인, 섹션 타이틀, 메타 텍스트, 액션 텍스트 체계 분리
- 간격: 화면 패딩, 패널 간격, 카드 내부 간격을 토큰화
- 상태: saved, selected, error, paused, active step에 대한 시각 기준 통일

### 7.3 공통 컴포넌트 후보

- 앱 셸 네비게이션
- 섹션 패널
- 숫자 요약 카드
- 레시피 카드
- 재료 pill
- 상태 배지
- 선택 카드 / 선택 행
- 액션 바
- step list
- cook timer block

### 7.4 템플릿 구조 권장

- `base.html`: 공통 레이아웃, 토큰, 전역 버튼/폼/패널 스타일
- partial 또는 macro 후보
  - 레시피 카드
  - 상태 배지
  - 공통 액션 버튼 묶음
  - step row

## 8. 인터페이스 영향

기본 권장안에서는 아래를 변경하지 않습니다.

- 외부 API 라우트
- UI 라우트
- 서비스 메서드 시그니처
- DB 스키마
- 템플릿 컨텍스트의 핵심 키 이름

변경 가능한 범위:

- `base.html`의 공통 마크업 구조
- 각 템플릿의 레이아웃 계층
- CSS 클래스 구조
- 반복 블록의 partial/macro 분리
- 일부 버튼 텍스트, 섹션 타이틀, 상태 카피

## 9. 테스트 및 검토 포인트

문서 기준 검토 항목:

- 5개 화면이 모두 포함되어 있는가
- 각 화면마다 `유지 동작`과 `변경 포인트`가 분리되어 있는가
- 3가지 적용 방안에 복잡도, 장점, 단점, 리스크, 적합한 상황이 있는가
- 추천안이 현재 코드 구조와 충돌하지 않는가

구현 시 확인해야 할 핵심 동작:

- Home에서 랜덤 레시피 최대 8개 노출 유지
- Home 카드의 `Save/Unsave` 유지
- Fridge의 5개 선택 규칙 유지
- Recommendation의 선택 재료 컨텍스트 유지
- Recipe Detail의 shopping list 계산 결과 유지
- Cook Mode의 자동 step 전환과 pause/resume 유지

반응형 검토 포인트:

- Home 대시보드 숫자와 카드 배열
- Fridge의 고밀도 영역 세로 스택 전환
- Recipe Detail의 긴 스크롤 구간 정리
- Cook Mode의 타이머와 액션 고정 가시성

## 10. 실제 구현 순서 권장

1. `base.html` 재구성

- 공통 앱 셸
- 공통 토큰
- 버튼/패널/폼/배지 스타일 재정의

2. Home 전환

- 대시보드형 요약 구조
- 추천 카드 시각 체계 정리
- Grass 위치 재조정

3. Recipe Detail 전환

- 헤더 메타 구조 정리
- shopping list와 ingredients 분리 강화
- `Start Cooking` 우선 CTA 고정

4. Cook Mode 전환

- 집중형 레이아웃 적용
- 기존 JS 타이머 로직은 유지하면서 DOM 구조만 안전하게 재배치

5. Recommendation 전환

- 선택 재료 컨텍스트 강화
- featured + list형 카드 구조 적용 여부 판단

6. Fridge Management 전환

- 가장 복잡한 화면이므로 공통 컴포넌트가 준비된 뒤 재구성
- 입력 / preview / selection / edit 구조를 재편

7. 마무리 정리

- partial/macro 분리
- 공통 카피 정리
- 모바일 대응 보정

## 11. 최종 결론

Frigo의 현재 상태에서는 `Stitch` HTML을 그대로 옮기는 방식보다, `공통 셸 + 공통 토큰 + 화면별 단계적 재구성` 방식이 가장 현실적입니다.

즉, 이번 UI 변경은 프론트엔드 기술 전환이 아니라 아래 목표로 해석하는 것이 맞습니다.

- 현재 동작은 유지
- 정보 위계는 재설계
- 공통 시각 시스템은 새로 정리
- 화면은 우선순위에 따라 단계적으로 교체

이 방향이면 `Stitch` 시안의 장점을 흡수하면서도 현재 Frigo의 서버 렌더링 구조와 제품 흐름을 안정적으로 유지할 수 있습니다.
