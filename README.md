# The Giver v3 아키텍처

> [!IMPORTANT]
> **시스템 요구사항:** pi-agent ≥ 0.74.0 및 pi-subagents ≥ 0.24.3

## 메타포: 기억의 선택적 전달

| 《기억 전달자》(소설) | The Giver v3 (아키텍처) |
|---|---|
| 기억 전달자가 모든 기억을 통제 | **Giver**가 대화의 모든 컨텍스트를 독점 보유 |
| 수령자는 제한된 정보만 수신 | **P/S/W**는 Giver가 큐레이팅한 T₀만 수신 |
| 공동체는 Sameness에 거주 | **P/S/W**는 이전 이력이 없는 Fresh 상태로 실행 |
| 선택적이고 의도적인 전달 | T₀ → Tₖ 형태로만 정보 전달 (**giving**) |
| 고통의 전달 (giving of pain) | 실패 이력을 F[]에 담아 전달 → 다음 시도에서 회피 |
| Stirrings 감시 및 억제 | 실행 전후 Fresh 상태 보장, `"context": "fresh"` 필수 |

## 수학적 정의

### 시그니처

```
G:  user_input → H
P:  H → H
S:  H → H
W:  H → H
```

모든 서브에이전트는 H를 받아 H를 반환. G가 초기 H를 생성.

### 데이터 구조

```
T₀  = O + C + F[] + L[] + D[]       (G가 작성 — 초기 태스크 + 의존성)
Tₖ  = O + C + F[] + L[] + TF + D₀  (P가 Wₖ용으로 큐레이팅)
D   = (sig, path)                     (시그니처 + 파일경로 튜플)
D₀  = 초기 D[]의 큐레이팅              (Wₖ가 임포트하는 것만)
TF  = Target Files                    (W당 최대 3개)
R   = ok + msg + D[]                  (1/0, 자유텍스트, 새 시그니처)
H   = T₀ + D[] + TR₀ + TR₁ + ...    (평면 누적 히스토리)
```

### T₀ — 초기 태스크 (G가 작성)

```
### O     — Objective (단일, 한 문장)
### C     — Context (결정사항만, 대화 금지)
### F[]   — Failures (이전 실패 로그, 첫 시도면 "None")
### L[]   — Limits (기술적 제약)
### D[]   — Dependencies (타겟 외 임포트 시그니처 + 파일경로)
```

T₀의 모든 하위섹션은 P가 W에게 전달할 때 **큐레이팅**됨. 전체를 던지지 않고 W가 필요한 것만 추려서 Tₖ로 변환.

### Tₖ — Worker 태스크 (P가 큐레이팅)

```
### O     — 이 W에 맞게 큐레이팅된 목표
### C     — 이 W에 관련된 결정사항만
### F[]   — 이 W 범위의 실패만
### L[]   — 이 W에 해당하는 제약만
### TF    — 타겟 파일 (최대 3개)
### D₀    — 초기 D[]에서 이 W가 임포트하는 것만
```

### D의 두 출처

- **D₀** — T₀의 D[]에서 P가 큐레이팅 (계획 시점에 알던 것)
- **R.D[]** — W가 새로 만든 의존성 (실행 중에 생긴 것, 큐레이팅 없이 전부 누적)

## 체인 흐름

```
사용자 ↔ G (대화, 결정)
         │
         ▼
    G → T₀ 작성 (O + C + F[] + L[] + D[])
         │
         ▼
    ┌─── P (fresh, H 입력) ───────────────────────────┐
    │   │                                                │
    │   ├── S (fresh, H) ──→ R(S) ──→ H에 append       │
    │   │                                    │           │
    │   ├── T₀ 작성 ──→ H에 append          │           │
    │   │                                    │           │
    │   ├── W₀ (fresh, T₀+H) ──→ R₀ ──→ H에 append     │
    │   │                                    │           │
    │   ├── T₁ 작성 ──→ H에 append          │           │
    │   │                                    │           │
    │   ├── W₁ (fresh, T₁+H) ──→ R₁ ──→ H에 append     │
    │   │                                    │           │
    │   ├── ...                              │           │
    │   │                                    │           │
    │   ├── R.ok=0 → 중단, H를 G에 리턴     │           │
    │   └── 전부 성공 → H를 G에 리턴 ────────┘          │
         │
         ▼
    G → H 해석 → 사용자 보고
```

## H — 히스토리 (평면 누적)

H는 평면 마크다운 문서. 각 에이전트가 자기 출력을 append. `{previous}`가 H 누적 메커니즘.

```markdown
## T₀
### O
Add LRU caching to UserService

### C
User reported 800ms p99. Approved: in-memory LRU, 5-min TTL.

### F[]
None — first attempt

### L[]
Use lru-cache package. Max 1000 entries. Invalidate on CUD.

### D[]
getById(id: string): Promise<User | null> — src/services/user-service.ts
IStorage.get(key: string): Promise<string | null> — src/storage/interface.ts

---
## 0
### T₀
(add, update, delete caching in UserService)

### R₀
(Scout recon — dependency signatures)

---
## 1
### T₁
(implement cache layer in user-service.ts)

### R₁
ok: 1
D[]: (new signatures from implementation)

---
...
```

## 대원칙

1. **G는 대화 주체** — 사용자와 대화하고 결정, T₀를 작성
2. **T₀만 하류로 전달** — 대화 전체가 아닌 결정사항만
3. **모든 서브에이전트는 fresh** — `"context": "fresh"` 필수, 예외 없음
4. **P는 T₀를 Tₖ로 큐레이팅** — 전체를 던지지 않고 W에 맞게 추려서 전달
5. **TF는 최대 3개** — W당 타겟 파일 제한
6. **D₀는 큐레이팅, R.D[]는 누적 전달** — 초기 의존성만 추려서, 실행 중 새 의존성은 전부 전달
7. **D = (sig, path)** — "see xxx.ts" 금지, 실제 시그니처 + 파일경로 필수
8. **R.ok=0이면 즉시 중단** — 실패 시 G에게 H 리턴
9. **F[]에 실패 이력 누적** — 재시도 시 이전 실패 포함, 같은 실수 방지
10. **G는 파일 수정 금지** — 소스 코드 변경은 항상 체인(W)을 통해

## 파일 그룹핑

의존성 깊이 기준 정렬. 파일 수가 아닌 의존성 깊이가 분할 기준.

```
L₀ (프로젝트 임포트 없음): A, B       → W₁
L₁ (L₀ 임포트):            C, D       → W₂
L₂ (L₀-L₁ 임포트):         E, F       → W₃
```

| 파일 수 | 체인              | 배치 |
|---------|-------------------|------|
| 1-3     | P→S→W             | 1    |
| 4-6     | P→S→W→S→W        | 2    |
| 7-9     | P→S→W→S→W→S→W    | 3    |
| 3N      | P→(S→W)×N        | N    |

## 실패 프로토콜

체인 실패 시 F[]에 추가:

```
- What happened: (구체적: 에러 메시지, 잘못된 동작)
- Root cause: (WHY — T₀가 불충분했는지, P/W가 오해했는지)
- What to avoid: ("DO NOT modify X", "DO NOT use approach Y")
- Correct direction: (알려진 경우)
- Giver correction: (T₀가 불충분했으면 인정)
```

**모든 실패 후 필수 자기반성:**
- 정확한 위치를 지정했나? → 아니면 Giver 에러
- 모든 제약을 제공했나? → 아니면 Giver 에러
- 엣지케이스를 포함했나? → 아니면 Giver 에러

## 실패 분류

| 원인 | 패턴 | 해결 |
|------|------|------|
| 전략적 (G) | T₀ 불충분, 방향 오류 | Giver가 T₀ 수정 후 재시도 |
| 전술적 (P) | plan.md 잘못됨 | Giver가 P에 corrected context 제공 |
| 운영적 (W) | plan은 맞지만 구현 오류 | Pitfalls 업데이트 후 W 재시도 |

## 버그 진단 흐름

```
G → S (스카우트) → G → 사용자 ("원인: X, 옵션: A/B")
                                      │
                                      ▼
                               사용자 선택 → P→S→W 체인
```

## v2.5b에서 v3로의 변화

| v2.5b | v3 |
|-------|-----|
| 6섹션 Brief (Objective, Context, Prev Failures, DI, Target Files, Constraints) | T₀ = O + C + F[] + L[] + D[] |
| {previous}로 DI 수동 복사 | H 자동 누적 ({previous}) |
| JB → TB 별도 정의 | T₀ → Tₖ (같은 T家族) |
| J = JB + D[] 별도 | T₀에 D[] 포함 |
| 시그니처별 (G→J, P→R[], S→brief→R, W→T→R) | 통일 시그니처 (모두 H→H) |
| DI = 시그니처만 | D = (sig, path) 튜플 |
| R에 T 포함 | R = ok + msg + D[] (T 제외, 평면 나열) |

## 파일

| 파일 | 설명 |
|------|------|
| `.pi/agent/skills/giver/SKILL.md` | v3 Giver 스킬 정의 |
| `giver-principles.md` | v3 대원칙 (수학적 정의 + 구현체) |
| `docs/v25b-skill.md` | v2.5b 스킬 백업 |