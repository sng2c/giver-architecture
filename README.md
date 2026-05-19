# The Giver 아키텍처

> pi-subagents 프레임워크 기반으로 구현된 패턴입니다. `defaultContext: fresh` 설정과 `{previous}` 체인 변수, `context.md`/`plan.md` 파일 전달 등은 pi-subagent의 기능을 활용합니다.

## 메타포

> *"기억을 전달받는다면, 그건 온전한 기억이어야 한다."*
> — 로이스 로리, 《기억 전달자》

《기억 전달자》에서 한 사람이 세상의 모든 기억을 품는다. 나머지 모든 사람은 **Sameness** 속에 산다 — 역사도, 맥락도, 축적된 노이즈도 없이. 기억 전달자는 필요한 순간에 필요한 기억만 골라 전달한다. 꿈 공유(giving of pain)를 통해 고통의 기억도 전달하여 같은 실수를 반복하지 않게 한다.

이 아키텍처도 똑같이 작동한다:

| 《기억 전달자》(소설) | The Giver (아키텍처) |
|---|---|
| 기억 전달자가 모든 기억을 보유 | Giver가 모든 대화 컨텍스트를 보유 |
| 수령자는 전달받은 것만 받음 | Planner는 Giver의 브리프만 수신 |
| 공동체는 Sameness 속에 삶 | Worker/Scout는 완전히 fresh — 역사 0 |
| 전달은 선택적이고 의도적 | **tx**는 Planner에게만 명시적 6섹션 계약 |
| 기억은 사라지지 않고 보류만 됨 | 대화 컨텍스트는 Giver에만 머물고 아래로 새지 않음 |
| 꿈 공유로 고통을 전달 | **Dream Sharing**으로 실패를 전달하여 반복 방지 |

## 설계 철학

### 문제
단일 에이전트 세션에서는 모든 도구 호출, 파일 읽기, 대화 턴이 컨텍스트에 **누적**된다. 200번째 턴은 앞선 199개 턴을 모두 다시 지불한다. 토큰이 기하급수적으로 쌓이고, 노이즈가 신호를 삼킨다. 300번째 턴이면 에이전트는 191K 토큰의 역사를 헤치고 단순 수정 하나 하러 간다.

Fork 모드(상위 컨텍스트 상속)는 더하다. 자식은 상위의 누적된 전체 컨텍스트를 복사한 채 시작하고 거기에 자신의 것까지 더한다. 양쪽 다 복리로 쌓인다.

### 해결: 3개 층, **tx** (transmission), Dream Sharing, 주기적 압축

```mermaid
graph TD
    G["Giver\n컨텍스트 보유"]
    P["Planner\nFRESH"]
    S1["Scout\nFRESH"]
    S2["Scout\nFRESH"]
    W["Worker\nFRESH"]

    G -->|"tx (6섹션 계약)"| P
    P -->|"plan.md\n(Worker Briefing 포함)"| S2
    S1 -->|"코드 정찰"| P
    S2 -->|"구현 정찰"| W

    G -.->|"Dream Sharing\n(재시도 시 Planner 브리프에 포함)"| P
    P -.->|"Pitfalls 섹션으로\nplan.md에 반영"| W

    style G fill:#4a9eff,color:#fff,stroke:#2d7ce0
    style P fill:#f5a623,color:#fff,stroke:#d4901e
    style W fill:#7ed321,color:#fff,stroke:#5fb818
    style S1 fill:#7ed321,color:#fff,stroke:#5fb818
    style S2 fill:#7ed321,color:#fff,stroke:#5fb818
```

**브리핑 책임:** Giver가 Planner를 브리핑하고, Planner가 Worker를 브리핑한다. Worker가 받는 지시는 plan.md의 **Worker Briefing** 섹션이다 — Key Decisions, Pitfalls & What to Avoid, Constraints, Scope Boundary.

**Worker 입력 (대화 기록 없음):**

| 소스 | 내용 |
|---|---|
| plan.md | Planner가 작성한 구현 계획 + Worker Briefing |
| {previous} | 직전 scout의 코드베이스 리컨 |
| context.md | scout가 작성한 코드 컨텍스트 |
| 직접 읽은 코드 | worker가 자체적으로 읽은 파일 |

### 핵심 원칙 (6개)

1. **The Giver가 유일한 컨텍스트 보유자.** 지저분한 대화 기록은 Giver에만 있다. 아래로는 절대 흐르지 않는다.

2. **tx가 전달 수단.** Giver는 전체 기억을 쏟지 않는다 — Planner에게만 **tx** (transmission)로 6섹션 브리프를 선택적으로 전달한다:
   - **Objective** — 무엇을, 왜
   - **Context** — fresh 에이전트가 볼 수 없는 모든 것
   - **Previous Failures** — 이전 시도의 실패 기록 (Dream Sharing)
   - **Target Files** — 어디에 작업할지
   - **Constraints** — 하지 말아야 할 것
   - **Scope Boundary** — 범위 안과 밖

3. **Planner가 Worker를 브리핑한다.** Giver는 Planner에게만 브리핑한다. Planner는 plan.md에 **Worker Briefing** 섹션을 작성하여 Key Decisions, Pitfalls, Constraints, Scope Boundary를 Worker에게 전달한다. Worker의 주 지시서는 plan.md다.

4. **실행은 Sameness 속에서.** Planner, scout, worker는 대화 기록 없이 시작한다. 매번 깨끗한 백지. 드리프트도, 노이즈도, 축적된 실수도 없다.

5. **Scout은 항상 worker 앞에.** Fresh worker에는 암묵적 코드 지식이 없다. Scout이 구현 직전에 `context.md`와 `{previous}`로 라이브 코드베이스 길잡이를 제공한다.

6. **Dream Sharing이 실패 반복을 방지한다.** Giver가 Planner 브리프의 `## Previous Failures`에 실패 경험을 전달하고, Planner가 이를 plan.md의 **Pitfalls** 섹션으로 번역하여 Worker에게 전달한다. 이 이중 변환이 실패 맥락을 실행 가능한 지시로 바꾼다.

7. **Giver가 방향을 결정하고 충분히 확전해야 한다.** Giver는 조직의 CEO와 같다. 방향이 모호하면 전체 조직이 틀린다. 브리프 전에 모호성을 해소하고, 충분히 탐색하고, 모든 제약을 명시해야 한다. Fresh 에이전트는 질문할 수 없다 — 추축으로 채우고, 추측은 잘못된 구현이 된다. Giver의 불충분한 브리프가 하류 오류의 진짜 원인인 경우, Giver가 자기 점검 없이 Planner/Worker를 탓하면 같은 모호한 브리프로 같은 실패가 반복된다.

8. **수집은 Giver가, 결정은 사용자가.** 코드베이스에 존재하는 정보는 Giver가 수집해야 하고(scout, 코드 읽기, 조사), 전략적 결정(접근 방식, 스코프, 트레이드오프)은 반드시 사용자가 내려야 한다. 사용자가 결정해야 할 전략적 선택을 Giver가 단독으로 결정하지 않고, 코드에서 찾을 수 있는 정보를 사용자에게 묻지 않는다.

9. **체인마다 브랜치.** 코드 변경이 포함된 모든 체인은 전용 git 브랜치에서 실행한다. 실패하면 `git checkout .`로 롤백, 성공하면 사용자가 머지 여부를 결정. Giver는 브랜치를 머지하지 않는다 — 보고만 한다. 모든 시도는 되돌릴 수 있다.

### 컨텍스트 압축: 선형 → 수렴

큐레이션 계층만으로는 기하급수가 아닌 **선형** 성장이 보장된다. 하지만 선형도 여전히 누적이다. 주기적 압축을 추가하면 상향선이 없는 톱니 패턴이 된다:

```mermaid
---
config:
    themeVariables:
        xyChart:
            plotColorPalette: "#4A9EFF"
---
xychart-beta
    title "컨텍스트 압축: 톱니 패턴"
    x-axis "턴" 0 --> 100
    y-axis "K 토큰" 0 --> 50
    line [5, 15, 25, 35, 45, 8, 18, 28, 38, 45, 8, 18, 28, 45]
```

- ↗ **체인 중**: 컨텍스트가 ~1K/턴 선형 증가 (5K → 45K)
- ↘ **압축 후**: Giver가 대화 히스토리를 구조화된 요약으로 교체, 기준선(~5-10K)으로 복귀
- 🔁 톱니 패턴 반복 → 상향선 없는 수렴 → **무한 세션 가능**

각 체인 완료 후:
1. Giver가 결과를 리포트
2. Giver가 컨텍스트가 무거워지면 직접 압축 — Dream Archive(실패 이력), Key Decisions, Current State를 보존하고 나머지 구현 세부사항은 드롭
3. 다음 체인의 브리프는 압축된 컨텍스트에서 도출

→ 선형 성장 + 주기적 압축 = **무한 세션이 가능**. 기하급수는 어떤 압축을 해도 결국 한계에 도달하지만, 선형 + 압축은 상향선이 없다.

### Dream Sharing: 실패 전달 프로토콜

The Giver 아키텍처의 3번째 핵심 기제. 큐레이션(tx)과 압축에 이은 세 번째 축.

Fresh 에이전트는 이전에 어떤 접근이 실패했는지, 왜 실패했는지, 무엇을 피해야 하는지 모른다. Dream Sharing은 이 실패 경험을 다음 시도에 전달하여 같은 실수의 반복을 방지한다.

**Dream Sharing이 없으면:**
- Worker가 라우트 레이어에 캐시를 구현 → 실패
- 다음 Worker도 같은 실수 → "The build failed. Try again." → 다시 같은 실수
- 3번째 Worker도 같은 실수 → 세 번의 낭비된 시도

**Dream Sharing이 있으면:**
- Worker가 라우트 레이어에 캐시를 구현 → 실패
- Giver가 Planner 브리프에 `## Previous Failures`로 구조화된 실패 기록 전달
- Planner가 이를 plan.md의 **Pitfalls** 섹션으로 번역: "DO NOT add caching in route handlers"
- 다음 Worker는 정확히 **무엇이, 왜, 어떻게** 실패했는지 알고 다른 접근 시도

실패 분류: Build Error, Logic Error, Wrong File, Wrong Approach, Partial Implementation, Cascade Failure, Scope Creep (7가지).

각 실패는 **What happened → Root cause → What to avoid → Correct direction** 4필드 구조로 전달. 재시도마다 브리프는 더 구체화된다 — 퍼널 패턴.

### 왜 작동하는가

| 문제 | Monolithic | Fork | The Giver | The Giver + 압축 |
|---|---|---|---|---|
| 컨텍스트 증가 | 기하급수 (26–42×) | 기하급수 (10–20×) | 선형 (10.1×) | **수렴 (톱니 패턴)** |
| 턴당 토큰 (P50) | ~100K | ~43K | ~21K | ~21K |
| 최대 단일 턴 | 191K | 44–99K | 45K | 45K |
| 세션 길이 제한 | 200K 한계 → 리셋 | 동일 | 선형 증가 | **무한** |
| Worker 컨텍스트 | 191K 누적 노이즈 | 상속 노이즈 | 5–15K 브리프 | 5–15K 브리프 |
| 실패 반복 | 같은 실수 반복 | 같은 실수 반복 | 같은 실수 반복 | **Dream Sharing으로 방지** |

### 측정 결과 (2026-05-18 실측)

- **Giver:** 93턴, P50=21K, 최대 45K, **선형 성장** (10.1×, ~1K/턴)
- **서브에이전트:** 740턴, P50=45K, 최대 117K, fresh 시작
- **Monolithic (과거):** P50≈100K, 최대 191K, **기하급수 성장** (26–42×)
- **핵심:** Tier 1의 100% 턴이 50K 이하에서 작동. Monolithic P10(20K)이 Giver P90(40K)과 동급.

## 파일

> pi agent v0.24.3 + pi-subagents 확장 기능 기준. `.pi/` 표준 경로에 배치.
>
> planner, worker는 pi-subagents 내장 에이전트의 `.pi/agents/` 오버라이드. `defaultContext: fresh` 설정만 오버라이드하고, 모든 행동 지시는 SKILL.md에 포함.

| 파일 | `.pi` 경로 | 설명 |
|------|-----------|------|
| `giver/SKILL.md` | `.pi/agent/skills/giver/SKILL.md` | The Giver 스킬 — tx 체인, Dream Sharing, Planner/Worker 행동 지시 포함 |
| `scout.md` | `.pi/agents/scout.md` | pi-subagents 내장 scout 오버라이드 — `defaultContext: fresh` 설정만 |

## Installation

Copy the `.pi/` directory structure to your project root:

```bash
cp -r .pi/ /your-project/.pi/
```

The skill will be activated automatically by pi-agent when the `giver` skill is triggered.

## Deploy

```bash
./scripts/deploy
```

Updates the GitHub gists with the latest versions of SKILL.md and README.md.

## License

MIT