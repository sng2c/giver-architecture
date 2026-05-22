# Giver 아키텍처 — 개선 이력

## 버전 진화

```
v1 → v2 → v2.1 → v2.2 → v2.3 → v2.4 → v2.5 → v2.5a → ... → v2.5i → v3.0 → v3.5 → ... → v3.5.8
격리  준수   진단    구조화   요약   연속    DI    구조강제       병렬분할  파이프라인        reads:false
```

---

## v3.5.8 — reads:false 사전 로딩 방지 (2026-05-22)

- 모든 chain step에 `"reads": false` 추가 (Planner + Worker 10개)
- Worker/Planner의 defaultReads(context.md, plan.md) 사전 로딩 방지
- Rule 3로 추가: chain 설정 규칙 (context:fresh, cwd, reads:false) 그룹화

## v3.5.7 — plan.md 제거 (2026-05-22)

- plan.md 제거: Planner가 plan.md를 작성하지 않음
- Worker가 Planner 개요를 읽지 않음
- H Document Format → RESULT Format 간소화
- Rule 6: (not plan.md) 참조 제거

## v3.5.6 — P→W×10 명시적 템플릿, 모순 제거 (2026-05-22)

- P→W×10 명시적 템플릿 (W1-W10)
- 병렬 workers 템플릿 제거
- TargetFiles: max 3 → 논리적 수정 그룹 할당
- H Document Format → RESULT Format (코드 본문 금지)
- Rule 5: previous Worker only → previous step (W1은 Planner 출력)
- Rule 6: (not plan.md) 참조 제거
- 모순 제거 (context.md 참조, 배치/Worker 용어 혼용 등)

## v3.5.5 — 논리적 수정 그룹 기준 (2026-05-21)

- ⌈files/3⌉ → 논리적 수정 그룹(logical modification groups) 기준 배치
- 같은 파일 여러 Worker 순차 수정 허용
- P→W×10 고정 체인 (Giver가 항상 10 Worker 슬롯으로 시작)
- Planner가 N(≤10) 결정, 미사용 슬롯은 no-op
- 최대 10 Workers 상한

## v3.5.4 — P→W×N 일반화 (2026-05-21)

- ⌈files/3⌉ 공식으로 Worker 수 결정
- 단일 체인 템플릿
- RESULT 1-based 인덱싱

## v3.5.3 — {previous} 단계 출력만 (2026-05-21)

- {previous}는 이전 단계 출력만 전달 (누적 아님)
- 실제 체인 데이터로 검증
- Giver는 progress.md에서 전체 결과 확인

## v3.5.2 — RESULT 포맷 간소화 (2026-05-21)

- RESULT → Files/Signatures/Summary (코드 본문 금지)
- {previous} 토큰 블로트 방지

## v3.5.1 — 한국어→영어 통일 (2026-05-21)

- SKILL.md 한국어/영어 혼용 → 영어 통일
- File Relationships 섹션 추가
- Task #0 용어 통일
- 7+ 파일 템플릿 수정

## v3.5 — Planner 파일 읽기 금지 (2026-05-21)

- Planner가 소스/테스트 파일 읽지 않음 (T₀에 모든 정보 포함)
- Planner 492K/46턴 → 30K/8턴 (−94%)

### v3.5 성능 (c2e86d3b 체인, 44 tests)

| 구조 | Planner | Worker 1 | Worker 2 | Worker 3 | **Total** |
|------|---------|----------|----------|----------|-----------|
| Monolithic | — | — | — | — | **864K** |
| v3.5 | 30K | 68K | 86K | 184K | **368K** |

Total −58%.

## v3.4 — Worker 템플릿 수정 (2026-05-21)

- Worker template {previous} 중복 수정
- RESULT format 간소화

## v3.3 — 분리 task 파일 (2026-05-21)

- Planner가 plan.md + task1.md, task2.md, task3.md 분리 작성
- Worker가 자신의 task 파일만 읽음
- Worker 1 입력: 301K→79K (−74%)

## v3.2 — Scout 제거, Planner 큐레이션 (2026-05-21)

- 체인 내 Scout 제거: P→S→W→S→W → P→W→W→W
- Planner가 T₀에서 Worker별 Imports needed 큐레이션
- Planner/Worker SCOPE: "within project root only"
- 부정 규칙 → 긍정 조건 패턴 (Do-When)

## v3.1 — Phase 1.5 Recon (2026-05-21)

- Giver가 T₀ 작성 전 Scout로 증상 영역 정찰 필수화
- Scout 결과를 Task #0 Imports needed에 반영
- 체인 밖에서 독립 호출 (Phase 1.5)

## v3.0 — 파이프라인 아키텍처 (2026-05-21)

v2.5i 이후 전면 재설계.

- P→S→W→S→W 체인 → P→W→W→W 단일 파이프라인 (체인 내 Scout 제거)
- Planner가 task{k}.md 분리 작성 (Worker 입력 −74%)
- Planner T₀에서만 큐레이팅 (Planner −94%)
- RESULT = Files/Signatures/Summary (코드 본문 제외)
- {previous}는 이전 단계 출력만 (누적 아님)
- 같은 파일 여러 Worker 순차 수정 허용
- Giver는 항상 P→W×10 체인 시작, Planner가 N(≤10) 결정
- task 파일 없는 Worker 슬롯은 no-op (즉시 종료)

---

## v2.5i — 독립 파일 병렬 Worker (2026-05-21)

### 근거
v2.5f에서 6파일/1체인 = Worker 180K 폭발. v2.5b는 6→1→3으로 분할해서 381K. 독립 파일은 병렬로 처리하면 시간/토큰 절약.

### 변경
- 의존성 기반 분할: 의존 → 직렬 chain, 독립 → 병렬 worker
- Layer 0(독립): 병렬 Worker 3개 동시 실행
- Layer 1(의존): 직렬 Chain, DI 포함

## v2.5h — 단일 Worker/직접 편집 금지 (2026-05-21)

### 근거
v2.5f에서 2가지 "When File Job → Chain" 위반: 체인 완료 후 직접 edit, Worker-only 단독 호출.

### 변경
- 금지 패턴 테이블: 빌드 에러 후 직접 edit → chain, Worker-only → 항상 chain, 작은 수정 → 1줄이어도 chain, 버그패치 → Scout → chain

## v2.5g — Scout 예산 완화 (2026-05-21)

### 근거
v2.5f에서 Scout 23K→Worker 180K (4.3배). v2.5b에서 Scout 63K→Worker 42K. Scout가 싸면 충분히 읽어야 Worker가 경량.

### 변경
- Scout 예산: 50K → 무제한 ("Scout 절약 = Worker 폭발" 명시)

## v2.5f — "When File Job → Chain" 프롬프트 제약 (2026-05-20)

### 근거
도구 제한은 leaky (bash 우회). 대신 조건-행동 패턴으로 명시.

### 실험 결과 (738K, 모놀리식 대비 +94%)

| 체인 | Scout | Planner | Worker | 합계 |
|------|-------|---------|--------|------|
| 1 | 23K | 17K | 180K 🔴 | 238K |
| 2 | 78K | 328K 🔴 | 94K | 500K |

- Giver가 1건 직접 edit (tsc 에러 수정)
- Planner 328K (예산 50K의 6.55배)
- v2.5b 대비 총 토큰 +94%

## v2.5e — 도구 제한 시도 (2026-05-20)

### 근거
v2.5d에서 Giver가 write/edit을 직접 호출 → 도구 자체를 차단.

### 결과
- `tools` frontmatter는 자식 에이전트에만 적용. 부모 도구 제한 불가.
- Giver가 여전히 write/edit 사용
- bash 우회 가능 → 도구 제한은 leaky
- chain 0건. 모놀리식 직접 구현.

## v2.5d — 토큰 예산 강제 (2026-05-20)

### 근거
"DI 충분한가?" 판단이 무한 후퇴. 예산 초과 = 자동 failover로 구조적 강제.

### 변경
- Worker 80K, Planner 50K, Scout 50K 예산
- 초과 시 자동 분할/DI 강화

### 결과: chain 0건, 모놀리식 직접 구현. Giver가 write/edit 직접 호출.

## v2.5c — 판단 완전 배제 (2026-05-20)

### 근거
Chain 3의 P→W 위반이 판단 기반 조건에서 비롯. 체인 구조를 판단이 아닌 체인 번호로 결정.

### 변경
- 체인 템플릿 고정 (Chain 1 → S→P→S→W 항상)
- SKILL.md 839→408줄 (−52%)

### 결과 (885K, 모놀리식 대비 −3%)
- 체인 구조 100% 준수 하지만 분할 전략 실패
- 4파일 1체인 → Planner 366K + Worker 244K
- v2.5b는 같은 파일 2체인으로 227K

## v2.5b — Do-When 패러다임 전환 (2026-05-20)

### 근거
MUST/NEVER/PROHIBITED → 모델이 무시. 조건-행동 패턴으로 전환.

### 결과 (381K, 모놀리식 대비 −56%)

| 체인 | 구조 | Worker | DI | SCOPE |
|------|------|--------|:--:|:-----:|
| 1 | S→P→S→W ✅ | 42K 🟢 | ✅ | ✅ |
| 2 | S→P→W | 103K 🟡 | ✅ | ✅ |
| 3 | **P→W ⚠️** | 37K 🟢 | ✅ | ✅ |

- DI/SCOPE 포함 → 모든 Worker ≤103K
- 낭비율 34% → 6%
- Chain 3 P→W 위반 → 판단 무한 후퇴 발견

## v2.5a — 구조적 준수 강제 (2026-05-19)

### 근거
v2.5 clean run이 체인 구조를 무시 → 금지형 규칙만으로는 부족.

### 결과
- P→S→W 실행 → 잘못된 경로로 실패
- Giver가 Worker-only로 우회 (290K)
- 체인 준수: ❌
- 인사이트: prohibit 기반 규칙은 모델이 예외 상황을 자의 해석해서 무력화

## v2.5 — 의존성 인터페이스 (2026-05-19)

### 근거
v2.4 Worker 209K → "see xxx.ts"로 DI 미제공 → Worker가 의존성 파일 직접 읽음.

### 변경
- 🔴 의존성 인터페이스(DI) 제공 ("see xxx.ts" 금지)
- 🔴 Worker SCOPE 자급자족
- 🟡 의존성 깊이 기반 분할

### 결과 (3회)
- 1차: 443K, failback 정상
- 2차: ⚠️ Giver가 P→S→W 무시하고 Worker 직접 호출 (238K 🔴)
- 분석: "ALWAYS use P→S→W" 금지형 규칙은 준수율 낮음

## v2.4 — 연속 실행 (2026-05-19)

### 근거
다중 체인 시 사용자 확인 대기 → 불필요한 지연. 무조건 재시도 → 과도 읽기.

### 통제 실험 (redbis-coding-test)

| 체인 | Planner | Scout | Worker | 합계 | 이상적 |
|------|--------:|------:|-------:|-----:|:------:|
| 1 | 31K 🟢 | 14K 🟢 | 170K 🟡 | 214K | 2/3 |
| 2 | 46K 🟢 | 14K 🟢 | 77K 🟢 | 137K | 3/3 |
| 3 | 49K 🟢 | 31K 🟢 | 209K 🟠 | 288K | 2/3 |
| **총합** | | | | **640K** | **7/9** |

vs 모놀리식 857K: −25%

## v2.3 — 요약 강화 (tag 019931c)

### 근거
desync 사태에서 Planner가 이전 체인 전체 출력(3.3M) 복사 → 낭비 폭발.

### 변경
- 🔴 Previous Failures 요약 필수
- 🔴 Planner 과도 읽기 금지

## v2.2 — 구조화 (2026-05-20)

### 근거
태스크 분할 준수율 0%, Scout 타겟팅 40% → 구조적 체크리스트 필요.

### 결과
- Planner 61K 🟢, Scout 59K 🟢
- desync 버그 발견: 4회 재시도로 1.85M, 83% 낭비

## v2.1 — 협업 진단 (2026-05-20)

### 근거
Planner가 버그 원인을 독자적으로 진단 → 사용자 개입 기회 없음.

### 결과 (7체인)
- Planner 평균: 513K → 182K (−64%)
- Phase 0.5 준수율: 75%

## v2 — 격리 복원 (2026-05-19)

### 근거
v1의 97% 낭비율이 `context:"fork"` 상속에서 비롯됨.

### 변경 6건
1. 🔴 `context:"fresh"` 모든 호출에 명시 → fork 0건
2. 🔴 `context:"fork"` 금지
3. 🟡 Scout 타겟팅 → Scout −62%
4. 🟡 Target Files "Unknown" 금지 → Worker −25%
5. 🟢 3+ 파일 태스크 분할
6. 🔴 체인당 Worker 1개

### 결과
- fresh 100%, fork 0건
- Scout 275K → 105K (−62%)

## v1 — 베이스라인 (2026-05-19)

초기 프로토콜. 토큰 효율 분석으로 심각한 문제 발견.

| 지표 | v1 |
|------|-----|
| `context:"fresh"` 명시율 | 3% |
| Fork 호출 | 8건 (최대 7.6M 누수) |
| Scout 평균 | 275K |
| Planner 평균 | 691K |
| Worker 평균 | 1.9M |
| Worker 이상적(≤80K) | 0% |
| 낭비율 | ~97% |

---

## 인사이트 축적

### 준수율과 규칙 형태의 상관관계

| 규칙 형태 | 준수율 | 예 |
|-----------|--------|---|
| Auto-repeat (템플릿 내 지시) | ~100% | JSON의 `"context": "fresh"`, Worker SCOPE 지시 |
| Structural (구조적 조건) | ~100% | 체인 번호, 체크리스트 |
| Do-When (조건→행동) | ? | v2.5c 재실험 필요 |
| Prohibit (NEVER/MUST) | 0-4% | "NEVER invoke worker directly" |

### 판단 무한 후퇴

```
"DI 충분한가?"          → 모름
  "DI 출처가 확실한가?"   → 모름
    "확실 여부는?"        → 모름
```

모든 판단 조건은 한 단계 더 깊은 판단을 요구. 유일한 해결: 판단 자체를 제거하고 구조로 대체.

### 모놀리식 vs Giver 토큰 비교

```
모놀리식  ████████████████████████████████████████████ 857K 🔴
v2.5c     ██████████████████████████████████████████████ 885K 🔴
v2.5f     ████████████████████████████████████          738K 🔴
v2.4      ███████████████████████████                  640K 🟠
v2.5b     ████████████████                             381K 🟡
v3.5      ██████████████████                           368K 🟡 ⭐
이상적     ████                                        ~80K 🟢
```

### Worker 토큰 감소 추이

```
v2.5c C1 ██████████████████████████████████████████████ 244K 🔴
v2.5f C1 ████████████████████████████               180K 🔴
v2.4 C3 ██████████████████████████████               208K 🟠
v2.4 C1 ████████████████████                        170K 🟡
v2.5f C2 ██████████████████████████                 103K 🟡
v2.5b C2 ████████████████                            103K 🟡
v2.5a   ████████████████                            144K 🟡
v2.5b C1 █████                                        42K 🟢
v2.5b C3 █████                                        37K 🟢
v3.5 C1 █████████████                                 68K 🟢 ⭐
이상적    █████                                        80K 🟢
```

---

## Git 태그

| 태그 | 설명 |
|------|------|
| v1 | 베이스라인 |
| v2 | 격리 복원 |
| v2.1 | 협업 진단 |
| v2.2 | 구조화 |
| v2.3 | 요약 강화 |
| v2.4 | 연속 체인 |
| v2.5 | 의존성 인터페이스 |
| v2.5b | do-when 전환 |
| v2.5c | 판단 배제 + 템플릿화 |
| v2.5d | 토큰 예산 강제 |
| v2.5e | 도구 제한 시도 (leaky 실패) |
| v2.5f | file-job 프롬프트 제약 |
| v2.5g | Scout 예산 완화 |
| v2.5h | 단일 Worker/직접 편집 금지 |
| v2.5i | 독립 파일 병렬 Worker |
| v3.5.2 | RESULT 포맷 간소화 |
| v3.5.3 | {previous} 단계 출력만 |
| v3.5.4 | P→W×N 일반화 |
| v3.5.5 | 논리적 수정 그룹 기준 |
| v3.5.6 | P→W×10 명시적 템플릿 |
| v3.5.7 | plan.md 제거 |
| v3.5.8 | reads:false 사전 로딩 방지 |