# Giver 아키텍처 - 개선 이력

## 버전진화

```
v1 → v2 → v2.1 → v2.2 → v2.3 → v2.4 → v2.5 → v2.5a → v2.5b → v2.5c → v2.5d → v2.5e → v2.5f → v2.5g → v2.5h → v2.5i
격리  준수   진단    구조화   요약   연속    DI    구조강제  do-when  판단배제  예산강제  도구제한  file-job  Scout완화  단일금지  병렬분할
```

---

## v1: 베이스라인 (2026-05-19)

초기 프로토콜. 토큰 효율 분석으로 심각한 문제 발견.

**관측 결과 (PTT 프로젝트, 52세션):**

| 지표 | v1 |
|------|-----|
| `context:"fresh"` 명시율 | 3% |
| Fork 호출 | 8건 (최대 7.6M 누수) |
| Scout 평균 | 275K |
| Planner 평균 | 691K |
| Worker 평균 | 1.9M |
| Worker 이상적(≤80K) | 0% |
| 낭비율 | ~97% |

**핵심 문제:** fork 상속으로 부모의 방대한 컨텍스트가 하위 에이전트에 그대로 누수됨.

---

## v2: 격리 복원 (2026-05-19)

### 근거
v1의 97% 낭비율이 `context:"fork"` 상속에서 비롯됨을 확인.

### 변경 6건

| # | 항목 | 근거 | 효과 |
|---|------|------|------|
| 1 | 🔴 `context:"fresh"` 모든 호출에 명시 | v1: 97% 미지정 | fork 0건, fresh 100% |
| 2 | 🔴 `context:"fork"` 금지 | v1: 8건 fork | fork 0건 |
| 3 | 🟡 Scout 타겟팅 지시 | Scout 평균 275K | Scout -62% |
| 4 | 🟡 Target Files에 "Unknown" 금지 | Worker 과도한 코드 리딩 | Worker -25% |
| 5 | 🟢 3+ 파일 태스크 분할 | 대형 리팩토링 Worker 과다 | 검증 필요 |
| 6 | 🔴 체인당 Worker 1개 | 다중 Worker가 Giver 평가 우회 | 1 Worker/chain |

### 결과
- fresh 100%, fork 0건 달성
- Worker 버그 수정 8K 🟢 달성
- Scout 275K → 105K (-62%)

---

## v2.1: 협업 진단 (2026-05-20)

### 근거
Planner가 버그 원인을 독자적으로 진단하고 해결책을 선택 → 사용자 개입 기회 없음. "Gather what you can, decide what you must" 위반.

### 변경
Phase 0.5 도입: 버그/장애 시 Giver가 Scout로 증상 분석 → 사용자에게 옵션 제시 → 사용자 승인 후 구현 위임.

### 결과 (7체인, 26 subagent 호출)
- Planner 평균: 513K → 182K (**-64%**)
- Planner 최초 이상적 달성 (77K 🟢)
- Phase 0.5 준수율: 75%

---

## v2.2: 구조화 (2026-05-20)

### 근거
v2.1에서 태스크 분할 준수율 0%, Scout 타겟팅 40% → 구조적 체크리스트 필요.

### 변경 5건

| # | 항목 | 근거 | 효과 |
|---|------|------|------|
| 9 | 🟡 태스크 분할 트리거 확장 | 4.9M Worker 분할 미적용 | 검증 필요 |
| 10 | 🟡 Scout output limit 200→150줄 | Scout 평균 133K | ✅ 59K (-56%) |
| 11 | 🟢 Phase 1.5 파일 카운트 단계 | 태스크 분할 0% 준수 | 검증 필요 |
| 12 | 🟢 Phase 2/3 체크리스트 | Target Files "Unknown" 방지 | ✅ Target Files 지정 |
| 13 | 🟢 Scout 3요소 템플릿 구조화 | Scout 타겟팅 40% 준수 | ✅ 2/2 Scout 🟢 |

### 결과
- Planner 61K 🟢, Scout 59K 🟢
- 하지만 desync 버그 발견: 4회 반복 재시도로 1.85M 토큰, 83% 낭비

---

## v2.3: 요약 강화 (tag 019931c)

### 근거
desync 사태에서 Planner가 이전 체인의 전체 출력(3.3M)을 복사 → 낭비 폭발.

### 변경 3건

| # | 항목 | 근거 | 효과 |
|---|------|------|------|
| 14 | 🔴 Previous Failures 요약 필수 | Planner 3.3M 입력 | 전체 출력 복사 방지 |
| 15 | 🟡 Worker 파일 생성 강조 | Worker가 진행 보고서 작성 | 1차 체인에서 실패 |
| 16 | 🔴 Planner 과도 읽기 금지 | Planner 283K/301K | 스코프 외 파일 읽기 |

---

## v2.4: 연속 실행 (tag 698cf29)

### 근거
다중 체인 시 사용자 확인 대기 → 불필요한 지연. 반면 무조건 재시도 → 과도 읽기 원인.

### 변경 2건

| # | 항목 | 근거 | 효과 |
|---|------|------|------|
| 17 | 🟡 연속 체인 자동 실행 | 다중 체인 시 대기 | 3체인 한 번에 실행 |
| 18 | 🔴 재시도 시 사용자 결정 | 자동 재시도 금지 | 2번/3번 과도 읽기 분석 |

### 통제 실험 결과 (redbis-coding-test)

| 체인 | Planner | Scout | Worker | 합계 | 이상적 |
|------|--------:|------:|-------:|-----:|:------:|
| 1 | 31K 🟢 | 14K 🟢 | 170K 🟡 | 214K | 2/3 |
| 2 | 46K 🟢 | 14K 🟢 | 77K 🟢 | 137K | 3/3 |
| 3 | 49K 🟢 | 31K 🟢 | 209K 🟠 | 288K | 2/3 |
| **총합** | | | | **640K** | **7/9 (78%)** |

vs 모놀리식 857K: **+25% 절감**

---

## v2.5: 의존성 인터페이스 (tag 2e25b21)

### 근거
v2.4 체인 3 Worker 209K 🟠 → "see xxx.ts"로 DI 미제공 → Worker가 의존성 파일을 직접 읽음.

### 변경 3건

| # | 항목 | 근거 | 효과 |
|---|------|------|------|
| 19 | 🔴 의존성 인터페이스(DI) 제공 | "see xxx.ts" 금지 | Worker 과다 읽기 방지 |
| 20 | 🔴 Worker 스코프 자급자족 | brief에 모든 정보 포함 | Worker가 brief 외 파일 읽기 불필요 |
| 21 | 🟡 의존성 깊이 기반 분할 | 2파일+5의존성=208K vs 4파일+0의존성=170K | 깊이 > 파일 수 |

### 실험 결과 (3회)

**1차 (연결 오류 포함):**
- Chain 2 연결 오류 → Worker-only 재시도 75K 🟢
- 총 443K, 실패 시 failback 정상 작동 확인

**2차 (clean run):** ⚠️ **규칙 미준수**
- Giver가 P→S→W를 무시하고 Worker 직접 호출
- Worker 238K 🔴 - Scout 없이 과다 읽기
- 총 485K, 체인 준수 실패

**분석:** "ALWAYS use P→S→W" 금지형 규칙은 준수율이 낮음. 모델이 "더 빠른 길"을 판단해서 우회.

---

## v2.5a: 구조적 준수 강제

### 근거
v2.5 clean run이 체인 구조를 무시 → 금지형 규칙만으로는 부족. 구조적 강제 필요.

### 변경
- Scout를 모든 체인에 필수화
- Worker-only를 FAILBACK(2회 실패 후)으로 격하
- Failover 테이블로 회복 경로 명시
- "NEVER invoke worker directly" → "WHEN it fails, follow failover table"

### 실험 결과
- P→S→W 실행 → 잘못된 경로로 실패
- Giver가 **여전히** Worker-only로 우회 (144K+89K+57K = 290K)
- 체인 준수: ❌

**인사이트:** prohibit 기반 규칙은 모델이 "예외 상황"을 자의 해석해서 무력화.

---

## v2.5b: Do-When 패러다임 전환 (tag v2.5b)

### 근거
MUST/NEVER/PROHIBITED → 모델이 무시. 대신 조건-행동 패턴으로 전환.

### 변경
- ABSOLUTE RULES → Do-When Patterns (When X → do Y, otherwise → Z)
- Core Principles → Core Patterns (8개 when-pattern)
- Bug Fix Rule → do-when
- Task Splitting / DI / Consecutive chains → do-when 테이블
- 1086줄 → 843줄 (-22%)

### 실험 결과 (381K, +56% vs 모놀리식)

| 체인 | 구조 | Worker | DI | SCOPE |
|------|------|--------|:--:|:-----:|
| 1 | S→P→S→W ✅ | 42K 🟢 | ✅ | ✅ |
| 2 | S→P→W | 103K 🟡 | ✅ | ✅ |
| 3 | **P→W ⚠️** | 37K 🟢 | ✅ | ✅ |

**핵심 발견:**
1. DI/SCOPE 포함 → 모든 Worker ≤103K (v2.4 최대 208K 대비 -50%)
2. 낭비율 34% → 6%
3. 이상적 에이전트 78% → 88%
4. **Chain 3 P→W 위반** → Giver가 "2 파일이니 Scout 불필요"라고 판단

**판단 무한 후퇴 발견:**
```
"DI 충분한가?" → 모름
"DI 출처가 확실한가?" → 모름
"확실 여부는?" → 모름
```
→ 판단 조건은 검증 불가. 구조적 조건만 검증 가능.

---

## v2.5c: 판단 완전 배제 (tag v2.5c)

### 근거
Chain 3의 P→W 위반이 "when DI 출처가 확실" 같은 판단 기반 조건에서 비롯. 체인 구조를 판단이 아닌 체인 번호로 결정.

### 변경
- 체인 템플릿 고정: Chain 1 → S→P→S→W (항상), Chain N → P→S→W (항상)
- "files known/unknown" 조건 제거
- "DI 충분한가?" 질문 자체를 제거
- SKILL.md 전체를 템플릿+do-when 테이블로 재구조화 (839→408줄, -52%)
- prose 설명을 테이블/템플릿으로 교체

### 실험 결과 (885K, 모놀리식 대비 -3%)

| 체인 | 구조 | Worker | 문제 |
|------|------|--------|------|
| 1 | S→P→S→W ✅ | 244K 🔴 | 4파일 1체인 과부하 |
| 2 | P→S→W ✅ | - | Planner 366K 🔴 |

- 총 885K, 체인 구조 100% 준수 하지만 분할 전략 실패
- Layer 1+2 4파일을 1체인에 배분 → Planner 366K + Worker 244K
- 같은 4파일을 v2.5b는 2체인으로 분할 → 227K

### 기하급수 모델 검증

v2.5c Chain 2 실제 91.5K vs 예측 97.5K (7% 오차). DI 없으면 r≈2.5(기하급수), DI 있으면 r≈0.5(선형).

---

## v2.5d: 토큰 예산 강제 (tag v2.5d)

### 근거
"DI 충분한가?" 판단이 무한 후퇴. 예산 초과 = 자동 failover로 구조적 강제.

### 변경
- Worker 예산: 200K → 80K (1체인당)
- Planner 예산: 없음 → 50K (1체인당)
- Scout 예산: 없음 → 50K (1체인당)
- Failover 테이블: 예산 초과 시 자동 분할/DI 강화
- Giver가 "DI 충분한가?" 판단할 필요 없음. 초과하면 failover.

### 실험 결과: **chain 0건, 모놀리식 직접 구현**

Giver가 스킬을 로드하고 규칙을 인식했지만, write/edit을 직접 호출해서 9개 파일을 한 번에 작성. 체인 호출 없음.

**핵심 발견:** SKILL.md 규칙은 모델이 인식하지만, write 도구가 열려 있으면 "더 빠른 길"을 선택. 규칙 ≠ 행동.

---

## v2.5e: 도구 제한 시도 (tag v2.5e)

### 근거
v2.5d에서 Giver가 write/edit을 직접 호출 → 도구 자체를 차단하려 함.

### 변경
- SKILL.md frontmatter에 `tools: [subagent, read, bash, web_search, web_fetch]`
- write/edit 미포함 → Giver가 파일 작성 불가

### 문제 발견
1. `tools` 필드는 **자식 에이전트**에만 적용. 부모(메인 챗)의 도구를 제한하지 않음.
2. v2.5e 세션에서 Giver가 여전히 write/edit 사용 (chain 0건 + 1건 직접 edit)
3. bash로 `echo > file` 시 우회 가능 → 도구 제한은 leaky

**결론:** 도구 제한은 구조적 해결이 아님. 프롬프트 제약이 더 낫다.

---

## v2.5f: "When File Job → Chain" 프롬프트 제약 (tag v2.5f)

### 근거
도구 제한은 leaky (bash 우회). 대신 조건-행동 패턴으로 명시.

### 변경
- `tools` 필드 제거 (모든 도구 허용)
- 최상단에 "When File Job → Chain" 규칙 추가
- 파일 작업 테이블: 생성/수정/삭제 = chain, 읽기/빌드/git = 직접

### 실험 결과 (738K, 모놀리식 대비 +94%)

| 체인 | 구조 | Scout | Planner | Worker | 합계 |
|------|------|-------|---------|--------|------|
| 1 | S→P→S→W ✅ | 23K | 17K | 180K 🔴 | 238K |
| 2 | P→S→W ✅ | 78K | 328K 🔴 | 94K | 500K |

**긍정:** chain 0건(v2.5d) → chain 2건. "When File Job → Chain" 작동.

**문제:**
1. C1 Worker 180K — DI 불충분 → Worker가 파일 직접 읽음
2. C2 Planner 328K (예산 50K의 6.55배) — 21턴/25툴콜
3. Giver 1건 직접 edit (tsc 에러 수정)

### v2.5b vs v2.5f 비교

| 지표 | v2.5b | v2.5f | 차이 |
|------|------:|------:|------:|
| 총 토큰 | 381K | 738K | +94% |
| 체인 수 | 3 | 2 | -1 |
| Worker 최대 | 103K | 180K | +77K |
| Planner 최대 | 46K | 328K | +281K |

**핵심 차이:**
- 분할: v2.5b 6→1→3파일 vs v2.5f 6→4파일
- DI 품질: Scout 63K(v2.5b) → Worker 42K vs Scout 23K(v2.5f) → Worker 180K
- Planner 읽기: v2.5b 8턴/14툴콜 vs v2.5f 21턴/25툴콜

---

## v2.5g: Scout 예산 완화 (tag v2.5g)

### 근거
v2.5f에서 Scout 23K→Worker 180K (4.3배). v2.5b에서 Scout 63K→Worker 42K. Scout가 싸면 충분히 읽어야 Worker가 경량.

### 변경
- Scout 예산: 50K → 무제한 ("Scout 절약 = Worker 폭발" 명시)
- Scout 템플릿: OUTPUT LIMIT 150줄 제거, DI 수집 목적 명시
- Failover: Scout 예산 초과 시 수용 ("DI 수집이 Worker 경량화의 열쇠")

---

## v2.5h: 단일 Worker/직접 편집 금지 (tag v2.5h)

### 근거
v2.5f에서 2가지 "When File Job → Chain" 위반 발견:
1. 체인 완료 후 tsc 에러 → Giver가 직접 edit
2. 이전 세션에서 Worker-only 단독 호출 (Planner/Scout 없이)

### 변경
금지 패턴 테이블 추가:

| 패턴 | 위반 | 올바른 방법 |
|------|------|-------------|
| 빌드 에러 후 직접 edit | Giver가 파일 수정 | chain(P→S→W)으로 수정 |
| Worker-only 단독 호출 | Planner/Scout 없이 | 항상 chain |
| 작은 수정 직접 처리 | "1줄이니까" | 1줄이어도 chain |
| 버그패치 직접 작성 | Giver가 write/edit | Scout → chain |

예외 없음. 파일 작업은 항상 chain.

---

## v2.5i: 독립 파일 병렬 Worker (tag v2.5i)

### 근거
v2.5f에서 6파일/1체인 = Worker 180K 폭발. v2.5b는 6→1→3으로 분할해서 381K. 독립 파일은 병렬로 처리하면 시간/토큰 절약.

### 변경
Task Splitting 전면 개편:
- 의존성 기반: 의존 → 직렬 chain, 독립 → 병렬 worker
- Layer 0(독립): 병렬 Worker 3개 동시 실행
- Layer 1(의존): 직렬 Chain, DI 포함
- 병렬 Worker 조건: 파일 간 import 없음, Target Files 겹침 없음, 외부 DI는 plan.md 포함

```
Layer 0 (독립): config, logger, resp
  → 병렬 Worker 3개 동시 실행

Layer 1 (의존): parser, memory, sqlite  
  → Layer 0 완료 후 chain 실행, DI 포함

Layer 2+ (deep): handler, connection, server
  → Layer 1 완료 후 chain 실행
```

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
v2.4      ███████████████████████████               640K 🟠
v2.5f     ████████████████████████████████████      738K 🔴
v2.5c     ██████████████████████████████████████████ 885K 🔴
v2.5b     ████████████████                           381K 🟡
v2.5a*    ████████████                               290K    ← 규칙 위반
이상적     ████                                      ~80K 🟢
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
| v2.5g | Scout 예산 원화 |
| v2.5h | 단일 Worker/직접 편집 금지 |
| v2.5i | 독립 파일 병렬 Worker |

## 리포트

| 파일 | 설명 |
|------|------|
| `reports/baseline-v1-report.md` | v1 베이스라인 |
| `reports/v1-vs-v2-report.md` | v1 vs v2 비교 |
| `reports/v2.1-analysis-report.md` | v2.1 협업 진단 |
| `reports/v2.2-analysis-report.md` | v2.2 구조화 |
| `reports/v2.2-remaining-issues.md` | v2.2 잔존 과제 |
| `reports/redbis-comparison-report.md` | 모놀리식 vs Giver v2.2/v2.3 |
| `reports/monolithic-vs-v24-report.md` | 모놀리식 vs v2.4 통제 실험 |
| `reports/monolithic-vs-v25-report.md` | v2.5 실험 분석 |
| `reports/v25b-vs-v25f-report.md` | v2.5b vs v2.5f 비교분석 |