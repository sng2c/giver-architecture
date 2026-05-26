# Giver 아키텍처 — 개선 이력

## 버전 진화

```
v1 → v2 → … → v2.5i → v3.0 → v3.5.13 → v3.6
격리                      병렬분할   파이프라인  Signatures  Design Principles
```

---
## v3.6 — Design Principles, 리팩토링 설계 결정화 (2026-05-23)

- Design Principles 5개 추가 (GGON 번역): Minimally Invasive Change, Respect Centralized Control, Cognitive Load Management, Isolated Concerns, Refactor Value = Future-Cost Reduction
- 리팩토링 자동 금지 → Giver가 사용자에게 제안, 승인 시만 T₀ 포함
- Phase 2에 Refactoring Decisions 섹션 추가
- 모순 6건 수정: DP#4 읽기/수정 구분, DP#5 T₀ 기준 반영, History 정의 보완, Scout standalone 명시, 리팩토링 규칙 통합, Signature 정의 실제 동작 반영
- Scout Signature: History→History → recon→recon (called standalone, not in chain)

## v3.5.13 — Signatures 통합, Breaking forward, 모순 수정 (2026-05-22)

- Imports needed → Signatures로 통합 (같은 Dependency 튜플, 방향만 다름)
- T₀에 Target Files 필드 추가 (모순 #6 해결: Planner가 "Target Files in T₀" 참조 가능)
- T₀ 섹션 5→6개 (Target Files 추가)
- Breaking forward: Worker가 이전 Worker의 Breaking을 전달 → Wₖ+1이 W₁~Wₖ의 모든 Breaking 확인
- reads:false 설명 보강: defaultReads 프리로딩 방지, read 도구는 사용 가능
- Planner Working Rules: "T₀ Signatures가 충분하지 않을 때" Target Files 읽도록 보충
- Worker SCOPE: "files referenced in Signatures"로 정확화
- T₀ Signatures: "outside Target Files" → "both inside and outside Target Files"
- Constraints 중복 항목 제거, dependency signatures → Signatures 통일
- JSON T₀ template Constraints/Signatures placeholder 보강
- last Worker도 모든 RESULT 섹션 포함 (Giver가 progress.md에서 전체 확인)
- Pipeline 설명에 Breaking forward 명시
## v3.5.12 — Planner Target Files 읽기 허용, 실제 패턴 인라인 제공 (2026-05-22)

- Planner Working Rules: "read NO source or test files" → "You MAY read Target Files to extract implementation patterns"
- Rule 3: "Planner reads only T₀" → "Planner reads T₀ and may read Target Files to extract implementation patterns"
- Rule 12: Planner reads Target Files to extract key patterns inline
- Worker 과다 읽기 방지: Planner가 실제 코드 패턴(3-10 lines) 제공
## v3.5.11 — RESULT Breaking 섹션, aware+/− → Breaking 전환 (2026-05-22)

- RESULT 형식: 3섹션 → 4섹션 (Files, Signatures, Breaking, Summary)
- Breaking: Worker가 제거/변경한 export를 downstream Worker에게 전달
- "edit → fail → re-read" 루프 방지 — downstream Worker가 유효하지 않은 시그니처를 찾지 않음
- aware +/− 표기 제거 → Breaking 섹션으로 통일
- 리팩토링 시 Breaking에 import 변경 명시, 모든 import 사이트 업데이트
- Rule 15: Worker Breaking section이 downstream 실패를 방지
## v3.5.10 — Scout recon 강화: 파일 크기, 구현 패턴, 대형 파일 인식 (2026-05-22)

- Phase 1.5: Scout에 파일 크기(줄 수) + 구현 패턴(3-10줄) 요구 추가
- Scout 출력 제한: 150→200줄
- Giver T₀: 500줄 초과 → Constraints에 패턴 인라인, 2000줄 초과 → 리팩토링 고려
- Rule 12: Planner 대형 파일에 구현 패턴 포함 ("follow patterns" 금지)
- Rule 13: Planner 파일 크기 명시, 2000줄+ 리팩토링 Worker 배치 고려
- 리팩토링 주의: 새 인터페이스 생성, import 경로 변경, 공개 API 보존 필수
- Rule 3로 추가: chain 설정 규칙 (context:fresh, cwd, reads:false) 그룹화
## v3.5.9 — output:false (Planner plan.md 방지) (2026-05-22)

- Planner step에 `"output": false` 추가
- Rule 4: Planner step MUST include output:false
- Rule 리넘버링: chain 설정 규칙 1-4, chain 로직 5-14
## v3.5.8 — reads:false 사전 로딩 방지 (2026-05-22)

- 모든 chain step에 `"reads": false` 추가 (Planner + Worker 10개)
- Worker/Planner의 defaultReads(context.md, plan.md) 사전 로딩 방지
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
| v3.5.9 | output:false(Planner plan.md 방지), Rule 4 추가 |
| v3.5.10 | Scout recon: 파일 크기+구현 패턴, 리팩토링 주의 |
| v3.5.11 | RESULT Breaking 섹션, aware→Breaking 전환 |
| v3.5.12 | Planner Target Files 읽기 허용, 실제 패턴 인라인 |
| v3.5.13 | Signatures 통합, Breaking forward, T₀ Target Files, 모순 수정 |
| v3.6.2 | Task 파일 경로 근원 해결: output:"plan.md" + reads:["taskN.md"] |
## v3.6.5 — RESULT 포맷 개선 (2026-05)

- **RESULT "All tests pass" → "Verification passed"**: 전체 스위트를 돌렸다는 뉘앙스 대신 자기 검증만 통과했다는 의미. Worker가 검증 결과를 구체적으로 표현하도록 유도.

## v3.7.2 — W₁ Planner 출력 수신 제거 (2026-05)

- **W₁ {previous} 제거**: Worker 1의 태스크 템플릿에서 `{previous}` 참조 제거. W₁은 task1.md에서만 컨텍스트를 받음.
- **W₁ Breaking**: "forward Breaking items from {previous}" → "add this Worker's own" (W₁은 {previous}가 없으므로).
- **Rule 5 변경**: "{previous} carries previous step's output" → "W₁ does NOT receive Planner's text output. Wₖ(K≥2) receives {previous}=Wₖ₋₁'s RESULT."
- **Rule 7 변경**: "Worker 1 receives Planner output" → "Worker 1 does NOT receive Planner output. Worker K(K≥2) receives Wₖ₋₁'s RESULT."
- **Pipeline 다이어그램**: `W₁ → {previous} = Planner output` → `W₁ → NO {previous} (task file only)`
- **Signatures**: `W: Tₖ + {previous} → RESULT` → `W: Tₖ → RESULT (W₁: task file only; Wₖ≥2: task file + {previous})`

**근거**: Planner의 텍스트 출력은 "6 task files written" 확인 메시지. W₁은 task1.md에서 충분한 컨텍스트를 받으므로 Planner 출력은 토큰 낭비. 실측(66ecddfd 체인): Planner 출력 74,357토큰이 W₁에 전달되었지만 W₁은 task1.md만 참조함.

### R8 체인 실측 (Redbis double-ERR 수정, 66ecddfd)

| Step | Agent | Turns | Tokens | Result |
|------|-------|:-----:|-------:|--------|
| 0 | Planner | 30 | 74,357 | 6 task files + T₀ 가정 반전 발견 |
| 1 | Worker 1 | 12 | 22,955 | ✅ zset 3개 파일 |
| 2 | Worker 2 | 9 | 11,250 | ✅ string-ops |
| 3 | Worker 3 | 11 | 17,214 | ✅ stream 2개 파일 |
| 4 | Worker 4 | 10 | 18,266 | ✅ hash + json |
| 5 | Worker 5 | 10 | 15,481 | ✅ set/list/key/sort |
| 6 | Worker 6 | 9 | 17,020 | ✅ geo/bitmap/custom |
| 7 | Worker 7 | 2 | 2,537 | ⬜ No-op (task 없음) |
| 8-10 | — | — | — | 미할당 |

- **활성 Worker**: 7 (P + W1~W6)
- **총 토큰**: ~179,080
- **W₁에 전달된 Planner 출력**: 74,357토큰 (W₁은 참조하지 않음 → 낭비)
- **수정 파일**: 15개, 307줄 변경
- **테스트**: 1338/1338 통과, tsc clean
- **W₁ 토큰**: 22,955 (Planner 출력 74,357토큰 제거 시 약 30% 절감 예상)

### Completion Guard 문제

W₁~W6 작업 완료 후 W7이 no-op로 종료. Completion Mutation Guard가 "no edit made for implementation task"로 판단하여 체인 실패로 처리. 실제로는 모든 작업이 완료된 정상 종료. Giver가 progress.md에서 실제 결과를 확인하여 대응.

## v3.7.2 — 페르소나 기반 아키텍처, 검증 책임 명확화 (2026-05)

- **페르소나 도입**: 소설 The Giver의 캐릭터 역할을 에이전트 페르소나로 매핑. Giver = 기억 전달자(모든 맥락 보유, 직접 수정하지 않음), Planner = 배정 위원회(역할 분배만, 검증은 관심사外), Worker = 수령자/전문가(자기 범위 완전 책임).
- **Worker "owns its scope"**: 규칙("verify only your changes") → 정체성("you own your scope"). Worker가 자기 검증을 선택하는 게 아니라 자기 범위를 책임지는 전문가.
- **Giver "memory keeper"**: Phase 5에서 직접 수정 금지. 실패 시 Past failures에 기록하고 사용자와 대화. "고칠 수 있는 게 아니라, 기억으로 남긴다."
- **테스트 명령어 예시 제거**: Worker template에서 `npx vitest run src/__tests__/config.test.ts` 등 구체적 명령어 제거. b91d3d73에서 Worker가 예시의 `npx vitest run`을 전체 스위트로 확장하는 회귀 발견.
- **실측 근거**: b91d3d73에서 모든 활성 Worker가 `npx vitest run` 1338테스트 전체 스위트 실행. "각자 자기 범위만" 설명이 모델의 안전망 행동(전체 스위트)을 막지 못함. 템플릿 예시가 모델 행동에 강한 영향.

## v3.6.4 — 최소 책임 검증, T₀ Target Verification 제거 (2026-05)

- **Target Verification에서 협업 설명으로 전환**: Planner가 Worker에게 검증 대상을 지정하던 방식(v3.6.3)을 폐지. 대신 Worker에게 "다른 Worker가 각자 자기 범위를 담당하니, 네가 변경한 파일만 검증하면 된다"고 설명. 규칙("이 검증만 실행하라")은 어기지만 합리적 설명("각자 자기 범위만 하면 된다")은 따른다.
- **T₀/Tₖ에서 Target Verification 완전 제거**: T₀ 7섹션 → 6섹션. T₀에 Target Verification을 적고 Giver가 Phase 5에서 다시 읽는 건 순환이었다. Giver는 프로젝트 컨텍스트에서 바로 판단. Tₖ에도 삭제.
- **Planner 복사 회귀 구조적 방지**: f7ef943b에서 Planner가 T₀의 Target Verification(`npx vitest run`)을 모든 Worker에 복사 → tk/byte 49×. T₀에 검증 명령어가 없으면 Planner가 복사할 수 없음.
- **Worker 자가 판단**: Worker가 자기 변경 범위를 스스로 판단하여 관련 테스트만 실행. Planner 개입 없이 합리적 자기이해로 동작.
- **실측 근거**: f7ef943b에서 Planner가 모든 Worker에 전체 스위트 지정 → tk/byte 12×(최소검증)에서 49×(전체스위트)로 4배 악화. Planner 컴플라이언스가 v3.6.3의 취약점이었음.

## v3.6.3 — Target Verification scope, 최소 책임 원칙 (2026-05)

- **Target Verification**: Worker가 검증할 명령어를 T₀/Tₖ에 명시. "run the relevant tests" → "run ONLY the verification commands listed in Target Verification"
- **최소 책임 원칙**: 각 Worker는 자기 Target Verification에 지정된 검증만 실행. 전체 테스트 스위트는 마지막 Worker 또는 Giver가 실행.
- **테스트 없는 프로젝트**: Target Verification이 비어있으면 `npx tsc --noEmit`, `cargo check`, `go build` 등 타입 체크/빌드로 검증.
- **언어별 예시**: TypeScript(npx vitest run, tsc --noEmit), Python(pytest, mypy), Rust(cargo test, cargo check), Go(go test, go build)
- T₀ 섹션이 6개에서 7개로 변경: Goal + Background + Past failures + Constraints + Target Files + **Target Verification** + Signatures
- **실측 효과**: 동일 과제(Redbis 44테스트)에서 v3.6.2 대비 W_tokens −75%, tk/byte 54×→12× (−78%). W3(server): 397K→20K (−95%). v3.6.3 tk/byte(12×)가 모놀리식(25×)보다 낮음.

## v3.6.2 — 2026-05-23

**Task 파일 경로 문제 근원 해결**

- **문제**: Planner가 cwd에 task 파일 작성 → 과거 실행 잔여 파일 오작동 위험
  - `reads:false` + `read` 도구: cwd에서 읽어서 작동은 하지만 잔여 파일 위험
  - `reads:["taskN.md"]`: chain directory에서 resolve → 파일 없음 → no-op
- **해결**: Planner `output:"plan.md"` → `[Write to:]` 프리픽스 주입 → chain directory 경로 확보
  - Planner가 chain directory에 task 파일 작성
  - Worker `reads:["taskN.md"]` → chain directory에서 resolve → 정상 작동
- **변경**:
  - Planner: `output:false` → `output:"plan.md"`
  - Worker: `reads:false` → `reads:["taskN.md"]`
  - Rule 3/4/6/8: reads override 양쪽 설명, output:[Write to:] 설명
  - Worker template: "Read taskN.md" → "Your task file taskN.md has been provided above"
  - Planner Working Rules: "to the [Write to:] directory"

## v3.7.2 — echo/RESULT 충돌 해결, "brief" 제거 (2026-05-26)

- **"Write a brief RESULT" → "Write a RESULT"**: "brief"가 "echo {previous}"와 충돌. 모델이 brief를 선택하여 echo를 건너뜀. 33588327 체인에서 모든 Worker가 echo 미준수.
- **W2+ 지시 변경**: "Echo the previous Worker result below, then write your RESULT" → "Reproduce the previous Worker result below, then write your RESULT". reproduce가 echo보다 강한 지시어.
- **v3.6.7에서 발견한 버그**: {previous}가 템플릿에서 3회 치환되어 Planner output이 Breaking 줄, Echo 지시줄, echo 위치에 중복 삽입. v3.6.7에서 1회로 수정.
- **Breaking forward는 지시 없이도 작동**: 33588327에서 W7이 W1~W6의 Breaking을 모두 forward. echo는 안 했지만 Breaking은 전달. 인사이트 #7 "지시보다 정체성" 재확인.

## v3.6.7 — {previous} 체인 echo, Breaking 템플릿 버그픽스 (2026-05-26)

- **{previous} 체인 echo**: W2+ output 앞에 `----\n{previous}\n----` 추가. 이전 Worker 결과를 체인으로 전달.
- **Breaking 템플릿 수정**: `{previous}`가 Breaking 줄 안에 들어있어 Planner output이 템플릿을 깨는 버그. Breaking 줄에서 `{previous}` 제거.
- **W1 Breaking**: "add this Worker's own" (이전 Worker 없음). W2+ Breaking: "forward all Breaking items from previous Workers above and add this Worker's own".
- **{previous} 3회→1회 치환**: 템플릿에서 `{previous}` 리터럴이 3곳에 있어 pi-subagents가 전부 치환. "contains RESULT #N"과 "Echo {previous}"를 정적 텍스트로 변경. echo 위치 1곳만 `{previous}` 유지.

## v3.7.2 — results.md 구조적 통신, {previous} 제거 (2026-05-26)

- **results.md 파일로 Worker 간 통신**: {previous} echo/reproduce 지시가 모델에 의해 무시됨 (v3.6.7, v3.6.8 실측). Breaking 수동 forward도 단일 홉 제한으로 이론적 간극 존재. results.md를 Worker가 append/reads하는 구조적 방식으로 교체.
- **reads 자동 주입**: W2+ reads=['taskN.md', 'results.md'] → pi-subagents가 results.md를 자동 주입. Worker가 안 읽을 수 없음.
- **append 지시**: 각 Worker가 작업 후 RESULT를 results.md에 append. 파일 쓰기는 소스 코드 쓰기와 같은 맥락에서 잘 지켜짐.
- **{previous} 완전 제거**: W1은 reads=['task1.md']만 (이전 결과 없음). W2+는 reads=['taskN.md', 'results.md'] (모든 이전 결과). Worker template에서 {previous}, echo, reproduce, "Context from previous", Breaking forward 모두 제거.
- **Breaking forward 불필요**: results.md에 모든 Worker의 Breaking이 누적. 수동 forward 지시 없이도 구조적으로 보장.
- **인사이트 #6 "지시보다 구조" 재확인**: echo 지시(v3.6.7), Reproduce 지시(v3.6.8) 모두 무시됨. 파일 reads 자동 주입은 구조적 — 지시 불필요. "검증 명령 제거"와 같은 패턴: 지시로 안 되면 구조로.

## v3.6.8 — echo/RESULT 충돌 해결, "brief" 제거 (2026-05-26)

- **"Write a brief RESULT" → "Write a RESULT"**: "brief"가 "echo {previous}"와 충돌. 모델이 brief를 선택하여 echo를 건너뜀. 33588327 체인에서 모든 Worker가 echo 미준수.
- **W2+ 지시 변경**: "Echo the previous Worker result below, then write your RESULT" → "Reproduce the previous Worker result below, then write your RESULT". reproduce가 echo보다 강한 지시어.
- **v3.6.7에서 발견한 버그**: {previous}가 템플릿에서 3회 치환되어 Planner output이 Breaking 줄, Echo 지시줄, echo 위치에 중복 삽입. v3.6.7에서 1회로 수정.
- **Breaking forward는 지시 없이도 작동**: 33588327에서 W7이 W1~W6의 Breaking을 모두 forward. echo는 안 했지만 Breaking은 전달. 인사이트 #7 "지시보다 정체성" 재확인.

## v3.7.2 — RESULT output + results.md 양쪽 기록 (2026-05-26)

- **v3.7.0 문제**: Worker가 output에 간단한 요약만 쓰고 results.md에만 RESULT 포맷 기록. "After writing your RESULT, append it to results.md"가 "output에 안 쓰고 results.md에만 써라"로 해석됨.
- **해결**: "Write your RESULT below. Also append it to results.md." — output에 RESULT 포맷을 쓰고, results.md에도 추가하라는 의미를 명확히 함.
- **실측 (67df5f65)**: W1~W5 전부 output에 RESULT 포맷 작성 ✅, results.md에 5개 RESULT 누적 (97줄) ✅, W2+ reads=['taskN.md', 'results.md'] 자동 주입 ✅.
- **W평균tk/t**: 19K (v3.6.8과 동급, 과제 차이가 더 큼).

## v3.7.0 — results.md 구조적 통신, {previous} 제거 (2026-05-26)

- **results.md 파일로 Worker 간 통신**: {previous} echo/reproduce 지시가 모델에 의해 무시됨 (v3.6.7, v3.6.8 실측). Breaking 수동 forward도 단일 홉 제한으로 이론적 간극 존재. results.md를 Worker가 append/reads하는 구조적 방식으로 교체.
- **reads 자동 주입**: W2+ reads=['taskN.md', 'results.md'] → pi-subagents가 results.md를 자동 주입. Worker가 안 읽을 수 없음.
- **append 지시**: 각 Worker가 작업 후 RESULT를 results.md에 append. 파일 쓰기는 소스 코드 쓰기와 같은 맥락에서 잘 지켜짐.
- **{previous} 완전 제거**: W1은 reads=['task1.md']만 (이전 결과 없음). W2+는 reads=['taskN.md', 'results.md'] (모든 이전 결과). Worker template에서 {previous}, echo, reproduce, "Context from previous", Breaking forward 모두 제거.
- **Breaking forward 불필요**: results.md에 모든 Worker의 Breaking이 누적. 수동 forward 지시 없이도 구조적으로 보장.
- **실측 (09a860c5)**: W1~W3 output에 RESULT 포맷 없음 (간단한 요약만), results.md에 3개 RESULT 누적. W2 input에 results.md 자동 주입 확인. v3.7.2에서 output에도 RESULT 기록하도록 수정.
- **인사이트 #10 "통신 채널은 구조로 보장한다"**: echo 지시(v3.6.7), Reproduce 지시(v3.6.8) 모두 무시됨. results.md reads 자동 주입은 구조적 — 지시 불필요. "지시보다 구조" (#6)의 확증.

## v3.7.2 — 동적 Worker 수, 같은 파일 순차 수정 병합, Planner task 파일 강제 (2026-05-27)

- **동적 Worker 수**: "Chain ALWAYS has fixed 10 Worker slots" 규칙 제거. Giver가 과제 범위에 따라 Worker 수를 결정 (simple=1, moderate=3~5, large=10). 1줄 수정 과제에 10개 슬롯이 다 돌면 9개 NOOP Worker가 ~170초 낭비.
- **같은 파일 순차 수정 병합**: "One file can be modified by multiple Workers in sequence" 규칙을 "merge them into one Worker"로 변경. 같은 파일을 여러 Worker가 순차 수정하면 직렬 실행이 강제되고 각 Worker가 전체 테스트 스위트를 재실행 (v3.7.1 실행: arg-parsers.ts 5 Worker 순차 수정, 5×1338 테스트).
- **Planner task 파일 강제**: Planner가 plan.md에 직접 내용을 쓰는 것을 방지. "DO NOT write to plan.md — plan.md is a system file" 지시 추가.
- **체인 34477324 실측**: 1줄 수정 과제에 10 Worker 슬롯이 전부 실행. W1만 작업(122초), W2~W10 NOOP(~170초 낭비, 전체의 58%). Planner가 task1.md를 안 만들고 plan.md에 직접 씀.
