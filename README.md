# The Giver v3 아키텍처

> [!IMPORTANT]
> **시스템 요구사항:** pi-agent ≥ 0.74.0 및 pi-subagents ≥ 0.24.3

## 7 Phase 워크플로우

```
Discuss → Recon → Decide → Task → Chain → Verify → Iterate
  ↑                                           │
  └───────────── 실패 시 돌아감 ───────────────┘
```

| Phase | 역할 | 행동 |
|-------|------|------|
| **Discuss** | 불명확 → 질문, 버그 → Scout 진단 | 사용자와 대화, 모호함 해소 |
| **Recon** | 코드 구조/시그니처 수집 | Giver가 파일을 직접 읽지 않고 Scout에게 위임 |
| **Decide** | 전략 결정, 대화 압축 | T_0에 넣을 결정사항만 추출 |
| **Task** | T_0 작성 | 5섹션 자연어 헤더로 문서화 |
| **Chain** | P→S→W 호출 | 파일 그룹핑, 배치 분할 |
| **Verify** | 테스트/검증, 결과 보고 | 실패 시 분류 |
| **Iterate** | 다음 단계 논의 | 필요시 재체인 |

## 메타포: 기억의 선택적 전달

| 《기억 전달자》(소설) | The Giver v3 (아키텍처) |
|---|---|
| 기억 전달자가 모든 기억을 통제 | **Giver**가 대화의 모든 컨텍스트를 독점 보유 |
| 수령자는 제한된 정보만 수신 | **P/S/W**는 Giver가 큐레이팅한 T_0만 수신 |
| 공동체는 Sameness에 거주 | **P/S/W**는 이전 이력이 없는 Fresh 상태로 실행 |
| 선택적이고 의도적인 전달 | T_0 → T_k 형태로만 정보 전달 (**giving**) |
| 고통의 전달 (giving of pain) | 실패 이력을 Past failures에 담아 전달 → 다음 시도에서 회피 |

## 데이터 구조

### 시그니처

```
G:  user_input → History
P:  History    → History
S:  History    → History
W:  History    → History
```

모든 서브에이전트는 `{previous}` 로 직전 스텝 출력만 받고, 자기 출력을 반환. 파일(plan.md, context.md)은 체인 전체에서 접근 가능.

### T_0 — Giver가 작성

```markdown
### Goal
한 문장 목표

### Background
결정사항만 (대화 내용 아님)

### Past failures
첫 시도면 "None — first attempt", 재시도면 구조화된 실패 로그

### Constraints
기술적 제약: 언어, 프레임워크, 패턴

### Imports needed
타겟 외 임포트 시그니처 + 파일경로
```

### T_k — Planner가 Worker별로 큐레이팅

```markdown
### Goal
이 Worker에 맞게 큐레이팅된 목표

### Background
이 Worker에 관련된 결정사항만

### Past failures
이 Worker 범위의 실패만

### Constraints
이 Worker에 해당하는 제약만

### TargetFiles
타겟 파일 (최대 3개)

### CuratedDeps
init Imports needed에서 이 Worker가 임포트하는 것만
```

### 핵심 정의

| 요소 | 정의 | 비고 |
|------|------|------|
| T_0 | Goal + Background + Past failures + Constraints + Imports needed | Giver 작성 |
| T_k | Goal + Background + Past failures + Constraints + TargetFiles + CuratedDeps | Planner가 Worker별 큐레이팅 |
| Dependency | (시그니처, 파일경로) | 튜플 |
| CuratedDeps | init Dependencies 큐레이팅 | Worker가 임포트하는 것만 |
| TargetFiles | 타겟 파일목록 | Worker당 최대 3개 |
| Result | 상태 + 메시지 + 새의존성 | 성공/실패, 자유텍스트 |

### Dependencies의 두 출처

- **CuratedDeps** — T_0의 Imports needed에서 P가 큐레이팅 (계획 시점에 알던 것)
- **New Dependencies** — Worker가 새로 만든 의존성 (실행 중에 생긴 것, 큐레이팅 없이 {previous}로 누적 전달)

---

## H — 히스토리 (평면 누적)

H는 `====` 구분자로 구분된 평면 마크다운. P는 PLAN, S는 RECON, W만 RESULT를 냄.

```markdown
----
Task #0 (Planner)

### Goal
Add LRU caching to UserService

### Background
User reported 800ms p99. Approved: in-memory LRU, 5-min TTL.

### Past failures
None — first attempt

### Constraints
Use lru-cache package. Max 1000 entries. Invalidate on CUD.

### Imports needed
getById(id: string): Promise<User | null> — src/services/user-service.ts
IStorage.get(key: string): Promise<string | null> — src/storage/interface.ts

====
PLAN
(plan.md: T_k 포함 — Worker Briefing)

====
RECON
(context.md: 리콘 — 의존성 시그니처)

====
RESULT #0 (Worker 1)

All tests pass.
## Dependencies (new signatures)
export class Logger { ... }
export function createLogger(module: string): Logger;

====
RECON
(2배치 리콘)

====
RESULT #1 (Worker 2)

All tests pass.
## Dependencies (accumulated)
...
```

---

## 체인 흐름

```
사용자 ↔ G (대화, 결정)
         │
         ▼
    G → T_0 작성
         │
         ▼
    P (fresh)
     │
     ├→ PLAN: plan.md에 T_k 포함
     ├→ S (fresh, {previous}=PLAN)
     │   └→ RECON: context.md 리콘
     ├→ W (fresh, {previous}=RECON)
     │   └→ RESULT #0: T_k 구현 + 새의존성
     │
     ├→ ... S→W 반복 ...
     │
     ├→ Result.상태=실패 → 중단, History를 G에 리턴
     └→ 전부 성공 → History를 G에 리턴

    G → History 해석 → 사용자 보고
```

---

## 파일 그룹핑

의존성 깊이 기준 정렬. 파일 수가 아닌 의존성 깊이가 분할 기준.

```
Layer 0 (프로젝트 임포트 없음): A, B       → Worker 1
Layer 1 (Layer 0 임포트):      C, D       → Worker 2
Layer 2 (Layer 0-1 임포트):    E, F       → Worker 3
```

| 파일 수 | 체인              | 배치 |
|---------|-------------------|------|
| 1-3     | P→S→W             | 1    |
| 4-6     | P→S→W→S→W        | 2    |
| 7-9     | P→S→W→S→W→S→W    | 3    |
| 3N      | P→(S→W)×N        | N    |

---

## 대원칙

1. **G는 대화 주체** — 사용자와 대화하고 결정, T_0를 작성
2. **T_0만 하류로 전달** — 대화 전체가 아닌 결정사항만
3. **모든 서브에이전트는 fresh** — `"context": "fresh"` 필수, 예외 없음
4. **P는 T_0를 T_k로 큐레이팅** — 전체를 던지지 않고 W에 맞게 추려서 전달
5. **TargetFiles는 최대 3개** — Worker당 타겟 파일 제한
6. **CuratedDeps는 큐레이팅, 새의존성은 누적 전달** — init 의존성만 추려서, 실행 중 새 의존성은 전부 전달
7. **D = (sig, path)** — 실제 시그니처 + 파일경로 필수, "see xxx.ts" 금지
8. **Result.상태=실패이면 즉시 중단** — 실패 시 G에게 H 리턴
9. **Past failures에 실패 이력 누적** — 재시도 시 이전 실패 포함, 같은 실수 방지
10. **G는 소스 코드 변경 시 항상 체인(W)을 통해** — G 자체는 파일 수정 안 함

---

## 실패 프로토콜

체인 실패 시 Past failures에 추가:

```
- What happened: (구체적: 에러 메시지, 잘못된 동작)
- Root cause: (WHY — T_0가 불충분했는지, P/W가 오해했는지)
- What to avoid: ("Do modify X only when fixing this specific bug")
- Correct direction: (알려진 경우)
- Giver correction: (T_0가 불충분했으면 인정)
```

**모든 실패 후 필수 자기반성:**
- 정확한 위치를 지정했나? → 아니면 Giver 에러
- 모든 제약을 제공했나? → 아니면 Giver 에러
- 엣지케이스를 포함했나? → 아니면 Giver 에러

### 실패 분류

| 원인 | 패턴 | 해결 |
|------|------|------|
| 전략적 (G) | T_0 불충분, 방향 오류 | Giver가 T_0 수정 후 재시도 |
| 전술적 (P) | plan.md 잘못됨 | Giver가 P에 corrected context 제공 |
| 운영적 (W) | plan은 맞지만 구현 오류 | Pitfalls 업데이트 후 W 재시도 |

---

## 버그 진단 흐름

```
G → S (스카우트) → G → 사용자 ("원인: X, 옵션: A/B")
                                      │
                                      ▼
                               사용자 선택 → P→S→W 체인
```

---

## Dependency Format

모든 의존성 시그니처에 파일경로 포함:

```
✅ getById(id: string): Promise<User | null> — src/services/user-service.ts
✅ IStorage.get(key: string): Promise<string | null> — src/storage/interface.ts
❌ see src/services/user-service.ts
```

시그니처를 모르면 Scout를 먼저 실행하여 수집.

---

## v2.5b에서 v3로의 변화

| v2.5b | v3 |
|-------|-----|
| 6섹션 Brief | T_0 = Goal + Background + Past failures + Constraints + Imports needed |
| {previous}로 DI 수동 복사 | H 자동 누적 ({previous}) |
| JB → TB 별도 정의 | T_0 → T_k (같은 Task家族) |
| JB + D[] 별도 정의 | T_0에 Dependencies 포함 |
| 시그니처별 (G→J, P→R[], S→brief→R, W→T→R) | 통일 시그니처 (모두 History→History) |
| DI = 시그니처만 | Dependency = (시그니처, 파일경로) 튜플 |
| R에 T 포함 | Result = 상태 + 메시지 + 새의존성 (평면 나열) |

---

## 기호 ↔ 자연어 대조표

| 기호 | 자연어 |
|------|--------|
| T | Task |
| T_0 | Task #0 (Giver가 작성) |
| T_k | Task #k (Planner가 Worker별로 큐레이팅) |
| O | Goal |
| C | Background |
| F[] | Past failures |
| L[] | Constraints |
| D | Dependency (시그니처, 파일경로) |
| D₀ | CuratedDeps |
| TF | TargetFiles |
| R | Result |
| H | History |

---

## 파일

| 파일 | 설명 |
|------|------|
| `.pi/agent/skills/giver/SKILL.md` | v3 Giver 스킬 정의 (6 Phase + 템플릿) |
| `giver-principles.md` | v3 대원칙 (수학적 정의 + 구현체) |
| `docs/v25b-skill.md` | v2.5b 스킬 백업 |
| `docs/v3-skill.md` | v3 초기 백업 |
| `docs/v3-principles.md` | v3 초기 원칙 백업 |
| `docs/v3-readme.md` | v3 초기 README 백업 |