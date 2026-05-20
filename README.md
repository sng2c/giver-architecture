# The Giver 아키텍처

> [!IMPORTANT]
> **종속성:** pi-agent ≥ 0.74.0 + pi-subagents ≥ 0.24.3 필요.
> 이 스킬은 pi-agent의 세션 관리, pi-subagents의 체인 실행, `{previous}` 변수, `defaultReads`, `output`, `context: "fresh"` 등에 종속됩니다.

## 종속성

| 기능 | 제공 | 사용 방식 |
|------|------|----------|
| `context: "fresh"` | pi-subagents 체인 API | 하위 에이전트를 fresh 세션으로 실행 |
| `{previous}` | pi-subagents 체인 변수 | 이전 스텝 출력을 다음 스텝에 전달 |
| `defaultReads` | pi-subagents 에이전트 설정 | planner가 `context.md`, worker가 `plan.md` 자동 읽기 |
| `output` | pi-subagents 에이전트 설정 | planner의 plan.md 자동 작성 |
| `chain` | pi-subagents 실행 모드 | 순차 체인 실행 (scout→planner→scout→worker) |
| `tasks` | pi-subagents 실행 모드 | 병렬 실행 (다중 worker) |
| `contact_supervisor` | pi-subagents 인터콤 | worker/planner가 Giver에게 에스컬레이션 |
| builtin planner/worker/scout | pi-subagents 에이전트 | 행동 지시는 SKILL.md에서, 설정만 빌트인 사용 |

## 메타포

> *"기억을 전달받는다면, 그건 온전한 기억이어야 한다."*
> — 로이스 로리, 《기억 전달자》

《기억 전달자》에서 한 사람이 세상의 모든 기억을 품는다. 나머지 모든 사람은 **Sameness** 속에 산다 — 역사도, 맥락도, 축적된 노이즈도 없이. 기억 전달자는 필요한 순간에 필요한 기억만 골라 전달한다. **고통의 전달(giving of pain)**을 통해 레거시의 고통스러운 진실 — 실패, 제약, 절대 피해야 할 것 — 을 정제하여 백지 상태의 수령자에게 주입한다.

이 아키텍처도 똑같이 작동한다:

| 《기억 전달자》(소설) | The Giver (아키텍처) |
|---|---|
| 기억 전달자가 모든 기억을 보유 | Giver가 모든 대화 컨텍스트를 보유 |
| 수령자는 전달받은 것만 받음 | Planner는 Giver의 브리프만 수신 |
| 공동체는 Sameness 속에 삶 | Worker/Scout는 완전히 fresh — 역사 0 |
| 전달은 선택적이고 의도적 | **giving**은 Planner에게만 명시적 6섹션 계약 |
| 기억은 사라지지 않고 보류만 됨 | 대화 컨텍스트는 Giver에만 머물고 아래로 새지 않음 |
| 고통의 전달 (giving of pain) | Giver가 실패 기억을 Planner에게 주입 → Planner가 Pitfalls로 번역 → Worker에게 전달 |
| Stirrings 감시 | 하위 에이전트 실행 전후 검증: 컨텍스트 오염 없는지 확인, fresh 보장 |

## 설계 철학

### 문제: 토큰의 복리

에이전트는 매 턴마다 이전의 모든 턴을 다시 입력으로 처리한다. 이것이 복리의 시작이다.

1. **누적 입력.** 도구 호출, 파일 읽기, 대화 내용이 컨텍스트에 쌓인다. 200번째 턴은 앞선 199개 턴을 모두 다시 입력으로 처리한다. 단순 버그 수정 하나에 191K 토큰의 역사를 헤치고 들어가야 한다.

2. **지시 희석.** 이전 대화의 볼륨이 커질수록 현재의 방향 지시(steering)가 희석된다. 그래서 지시를 점점 더 상세히 적게 되고, 상세한 지시는 또 입력을 키우고, 다시 희석되는 악순환이 된다.

3. **Fork는 병렬 작업으로 속도를 얻지만 배수로 낭비한다.** fork 모드에서 자식은 부모의 컨텍스트를 상속받아 즉시 작업할 수 있다. 별도 브리핑 없이 병렬로 시작할 수 있어 속도 이점이 있다. 하지만 상속받은 볼륨 전체를 매 턴마다 재처리해야 한다. 부모의 200K에 자식의 누적이 더해져 복리로 증가한다. 병렬로 얻은 속도가 배수의 낭비로 상쇄된다.

### 3-Tier 구조와 성능 추론

The Giver는 컨텍스트 관리를 3개 층으로 분리한다. 각 층의 역할과 토큰 예산이 명확하다:

<table>
<tr><th colspan="2" style="background:#1a2744">🏢 Giver (Context Keeper)</th></tr>
<tr><td colspan="2">
<b>역할:</b> 대화 기록 보유, 브리핑 작성, 실패 전달, 전략적 결정<br>
<b>토큰:</b> 선형 증가 → 주기적 압축 → 수렴 (톱니 패턴)<br>
<b>입력:</b> 사용자 메시지 + 하위 에이전트 결과<br>
<b>컨텍스트:</b> 전체 대화 보유, 하위로는 6섹션 브리프만 전달 (~5-15K)
</td></tr>
<tr style="background:#2a1a44"><th>📋 Planner (Fresh)</th><th>🔍 Scout (Fresh)</th></tr>
<tr><td>
<b>역할:</b> 구현 계획, Worker Briefing 작성<br>
<b>토큰:</b> ≤500K<br>
<b>입력:</b> 브리프 + 리컨<br>
<b>컨텍스트:</b> 대화 기록 0
</td><td>
<b>역할:</b> 코드 정찰, 타겟팅된 리컨<br>
<b>토큰:</b> ≤100K (타겟팅 시)<br>
<b>입력:</b> 타겟팅 지시만<br>
<b>컨텍스트:</b> 대화 기록 0
</td></tr>
<tr><th colspan="2" style="background:#1a3322">⚙️ Worker (Fresh)</th></tr>
<tr><td colspan="2">
<b>역할:</b> 코드 변경 실행<br>
<b>토큰:</b> ≤80K (이상적) — 브리프 + 리컨 + 대상 코드만<br>
<b>입력:</b> plan.md + {previous} + 대상 파일<br>
<b>컨텍스트:</b> 대화 기록 0, 구현에 필요한 정보만
</td></tr>
</table>

**이 구조가 토큰 절감을 만드는 추론:**

1. **Giver 층**은 전체 대화를 보유하되, 하위로는 6섹션 브리프(~5-15K)만 전달. 톱니 패턴 압축으로 상향선 없이 수렴.

2. **Planner/Scout 층**은 `context: "fresh"`로 실행. 부모의 191K 누적 노이즈를 상속하지 않음. Planner는 브리프+리컨만 수신(~50-500K). Scout는 타겟팅 지시만 수신(~30-100K).

3. **Worker 층**은 plan.md(Planner가 작성한 Worker Briefing) + 직전 Scout의 리컨 + 대상 파일만 수신. 이상적: 30-80K. 구현에 필요한 정보만, 대화 기록 0.

**Monolithic 대비 예상 효과:**

| 모델 | 컨텍스트 성장 | 총 입력 (200K cap) | Worker 입력 | 실패 전달 | Monolithic 대비 |
|------|-------------|-------------------|------------|----------|----------------|
| Monolithic | 기하급수 (재지불) | ~1,454M | 191K 누적 노이즈 | 없음 (같은 실수 반복) | 1× (기준) |
| Fork | 기하급수 (상속+증가) | >1,454M | 최대 7.6M 상속 | 없음 | <1× (더 악화) |
| The Giver (이론) | 수렴 (톱니) | **~130M** | **≤80K** 브리프만 | giving of pain | **~11×** |
| The Giver (v1 실측) | 수렴 | **620M** | 중앙값 1.1M | 22건 | **2.3×** |

이론적 절감은 Monolithic 대비 **11×**. v1 실측은 **2.3×**. 그 차이의 원인이 다음 절의 성능 검증 데이터로 드러난다.

### 해결: 3개 층, **giving** (transmission), giving of pain, 주기적 압축

```mermaid
graph TD
    G["Giver\n컨텍스트 보유"]
    P["Planner\nFRESH"]
    S1["Scout\nFRESH"]
    S2["Scout\nFRESH"]
    W["Worker\nFRESH"]

    G -->|"giving (6섹션 계약)"| P
    P -->|"plan.md\n(Worker Briefing 포함)"| S2
    S1 -->|"코드 정찰"| P
    S2 -->|"구현 정찰"| W

    G -.->|"giving of pain\n(재시도 시 Planner 브리프에 포함)"| P
    P -.->|"Pitfalls 섹션으로\nplan.md에 반영"| W

    style G fill:#4a9eff,color:#fff,stroke:#2d7ce0
    style P fill:#f5a623,color:#fff,stroke:#d4901e
    style W fill:#7ed321,color:#fff,stroke:#5fb818
    style S1 fill:#7ed321,color:#fff,stroke:#5fb818
    style S2 fill:#7ed321,color:#fff,stroke:#5fb818
```

**브리핑 책임:** Giver가 Planner를 브리핑하고, Planner가 Worker를 브리핑한다. Worker가 받는 지시는 plan.md의 **Worker Briefing** 섹션이다 — Key Decisions, Pitfalls & What to Avoid, Constraints, Scope Boundary.

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

### giving of pain: 실패 전달 프로토콜

Fresh 에이전트는 이전에 어떤 접근이 실패했는지, 왜 실패했는지, 무엇을 피해야 하는지 모른다. giving of pain은 이 실패 경험을 다음 시도에 전달하여 같은 실수의 반복을 방지한다.

각 실패는 **What happened → Root cause → What to avoid → Correct direction** 4필드 구조로 전달. 재시도마다 브리프는 더 구체화된다 — 퍼널 패턴.

### 핵심 원칙

1. **The Giver가 유일한 컨텍스트 보유자.** 지저분한 대화 기록은 Giver에만 있다. 아래로는 절대 흐르지 않는다.

2. **tx가 전달 수단.** Giver는 전체 기억을 쏟지 않는다 — Planner에게만 **giving** (transmission)로 6섹션 브리프를 선택적으로 전달한다:
   - **Objective** — 무엇을, 왜
   - **Context** — fresh 에이전트가 볼 수 없는 모든 것
   - **Previous Failures** — 이전 시도의 실패 기록 (giving of pain)
   - **Target Files** — 어디에 작업할지
   - **Constraints** — 하지 말아야 할 것
   - **Scope Boundary** — 범위 안과 밖

3. **Planner가 Worker를 브리핑한다.** Giver는 Planner에게만 브리핑한다. Planner는 plan.md에 **Worker Briefing** 섹션을 작성하여 Key Decisions, Pitfalls, Constraints, Scope Boundary를 Worker에게 전달한다. Worker의 주 지시서는 plan.md다.

4. **실행은 Sameness 속에서.** Planner, scout, worker는 `context: "fresh"`로 실행되어 대화 기록 없이 시작한다. 매번 깨끗한 백지. 드리프트도, 노이즈도, 축적된 실수도 없다.

5. **Scout은 항상 worker 앞에.** Fresh worker에는 암묵적 코드 지식이 없다. Scout이 구현 직전에 `context.md`와 `{previous}`로 라이브 코드베이스 길잡이를 제공한다.

6. **giving of pain이 실패 반복을 방지한다.** Giver가 Planner 브리프의 `## Previous Failures`에 실패 경험을 전달하고, Planner가 이를 plan.md의 **Pitfalls** 섹션으로 번역하여 Worker에게 전달한다. 이 이중 변환이 실패 맥락을 실행 가능한 지시로 바꾼다.

7. **Giver가 방향을 결정하고 충분히 확전해야 한다.** Giver는 조직의 CEO와 같다. 방향이 모호하면 전체 조직이 틀린다. 브리프 전에 모호성을 해소하고, 충분히 탐색하고, 모든 제약을 명시해야 한다. Fresh 에이전트는 질문할 수 없다 — 추축으로 채우고, 추측은 잘못된 구현이 된다. Giver의 불충분한 브리프가 하류 오류의 진짜 원인인 경우, Giver가 자기 점검 없이 Planner/Worker를 탓하면 같은 모호한 브리프로 같은 실패가 반복된다.

8. **수집은 Giver가, 결정은 사용자가.** 코드베이스에 존재하는 정보는 Giver가 수집해야 하고(scout, 코드 읽기, 조사), 전략적 결정(접근 방식, 스코프, 트레이드오프)은 반드시 사용자가 내려야 한다. 사용자가 결정해야 할 전략적 선택을 Giver가 단독으로 결정하지 않고, 코드에서 찾을 수 있는 정보를 사용자에게 묻지 않는다.

9. **버그픽스/트러블슈팅은 사용자와 협업 진단.** 원인 분석과 해결 방안 선택은 [Decide] 항목이다. Planner가 혼자 진단하고 수정하면 사용자가 동의할 기회가 없다. Giver는 먼저 scout으로 증상을 조사하고, 분석 결과와 수정 옵션을 사용자에게 제시한 후, 사용자가 원인과 접근 방식을 선택하면 그때 구현만 위임한다. Planner의 역할은 **사용자가 승인한 수정안의 구현 계획**뿐이다.

10. **체인마다 브랜치.** 코드 변경이 포함된 모든 체인은 전용 git 브랜치에서 실행한다. 실패하면 `git checkout .`로 롤백, 성공하면 사용자가 머지 여부를 결정. Giver는 브랜치를 머지하지 않는다 — 보고만 한다. 모든 시도는 되돌릴 수 있다.

### 왜 작동하는가

| 문제 | Monolithic | Fork | The Giver | The Giver + 압축 |
|---|---|---|---|---|
| 컨텍스트 증가 | 기하급수 (26–42×) | 기하급수 (10–20×) | 선형 (10.1×) | **수렴 (톱니 패턴)** |
| Worker 컨텍스트 | 191K 누적 노이즈 | 상속 노이즈 | 5–15K 브리프 | 5–15K 브리프 |
| 실패 반복 | 같은 실수 반복 | 같은 실수 반복 | 같은 실수 반복 | **giving of pain으로 방지** |

## 성능 검증

### v1 베이스라인 — 구조는 작동하지만 구현 갭이 크다 (52세션, 65 서브에이전트)

초기 프로토콜 적용 후 실제 세션 데이터로 베이스라인 측정. 3-Tier 구조의 이론적 이점(11× 절감)은 확인되었으나, 실제로는 2.3× 절감에 그침. 그 원인:

| 지표 | 이론적 목표 | 실측 | 갭 | 원인 |
|------|-----------|------|-----|------|
| Worker 입력 | ≤80K | 중앙값 1.1M | **14× 초과** | fork 누수, context 미지정, 과도한 코드 리딩 |
| `context:"fresh"` | 100% | 3% | **97% 갭** | 90%가 empty/default, fork 8건 |
| Scout 입력 | ≤100K | 평균 275K | **2.75× 초과** | 타겟팅 없는 exhaustive 리컨 |
| 총 토큰 | ~130M | 620M | **4.8× 초과** | 하위 에이전트 과다 실행이 누적 |

**3-Tier가 이론적으로는 작동하지만, 하위 에이전트가 `context:"fresh"` 없이 실행되면 상위 컨텍스트를 그대로 상속받아 Tier 분리가 무의미해진다.** 8건의 fork 호출(최대 7.6M)과 90%의 context 미지정이 3-Tier의 절연을 붕괴시킨 근원 원인.

> 상세 리포트: [`reports/baseline-v1-report.md`](reports/baseline-v1-report.md)

### v2 — Tier 절연 복원 (5체인, 12 서브에이전트)

v1의 6개 개선항목(fork 금지, `context:"fresh"` 100%, Scout 타겟팅, Target Files 명시, 태스크 분할, 체인당 Worker 1개) 적용. 3-Tier 절연이 복원되자 이론적 성능에 근접:

| 지표 | v1 | v2 | 변화 | 이론적 목표 대비 |
|------|-----|-----|------|---------------|
| Fork 호출 | 8건 (6%) | **0건** | ✅ ELIMINATED | 목표 달성 |
| `context:"fresh"` | 3% | **100%** | ✅ 완전 | 목표 달성 |
| Context 미지정 | 119건 (90%) | **0건** | ✅ ELIMINATED | 목표 달성 |
| Scout 평균 | 275K | **105K** | ✅ **-62%** | 이론 ≤100K에 근접 |
| Planner 평균 | 691K | **513K** | ✅ -26% | 개선 여지 있음 |
| Worker 평균 | 1.9M | **1.4M** | ✅ -25% | 단일 파일 버그 수정은 8K 🟢 |
| Worker 버그 수정 | — | **8K 🟢** | ✅ 이상적 도달 | ≤80K 목표 달성 |

**v2의 3-Tier 절연이 복원된 증거:** fork 0건, fresh 100% → Giver-Planner-Worker 간 컨텍스트 누수 완전 차단. 단일 파일 버그 수정(Chain 2)이 8K로 이론적 목표(≤80K)를 하회하며 3-Tier가 설계대로 작동함을 실증.

**잔존 과제:** Worker 3/5건이 🔴 과다. 전부 PTTPlugin.kt(1539줄 God Class) 추출로, **태스크 복잡도가 원인이지 3-Tier 결함이 아님.** 함수 단위 분할(Worker당 3-5개 함수)로 각 Worker 200K 이하 수렴 예상. 이는 Scout/Planner/Worker의 토큰 예산 문제가 아니라 태스크 분할 전략의 문제.

> 상세 리포트: [`reports/v1-vs-v2-report.md`](reports/v1-vs-v2-report.md)

### 개선 항목 이력

| # | 버전 | 항목 | 근거 | 효과 |
|---|------|------|------|------|
| 1 | v2 | 🔴 `context:"fresh"` 모든 호출에 명시 | v1: 97% 미지정 → fork/empty 누수 | fork 0건, fresh 100% 달성 |
| 2 | v2 | 🔴 `context:"fork"` 금지 | v1: 8건 fork, 최대 7.6M 누수 | fork 0건 달성 |
| 3 | v2 | 🟡 Scout 타겟팅 지시 (what/where/output limit) | v1: Scout 평균 275K | Scout 105K, -62% 달성 |
| 4 | v2 | 🟡 Target Files에 "Unknown" 금지 | v1: Worker 과도한 코드 리딩 | Worker -25% 달성 |
| 5 | v2 | 🟢 3+ 파일 태스크 분할 | v1: 대형 리팩토링 Worker 과다 | 검증 필요 (5+ 파일 태스크 미발생) |
| 6 | v2 | 🟢 브랜치 네이밍 프로젝트 컨벤션 존중 | v1: `giver/` 4% (2/52) | N/A (새 프로젝트에서 검증) |
| 7 | v2 | 🔴 체인당 Worker 1개 | v1: 다중 Worker가 Giver 평가 우회 | 5체인 모두 1 Worker/chain 달성 |
| 8 | v2.1 | 🔴 버그픽스/트러블슈팅 협업 진단 | Planner가 원인 진단 및 해결 선택 독자 결정 | 검증 필요 |

## 파일

| 파일 | 경로 | 설명 |
|------|------|------|
| `SKILL.md` | `.pi/agent/skills/giver/SKILL.md` | The Giver 스킬 — 전체 프로토콜 정의 |
| `pi-install` | `scripts/pi-install` | `~/.pi`에 심볼릭 생성 |
| `pi-analyze` | `scripts/pi-analyze` | 세션 로그 분석 — 토큰, 준수, 에러 분류 |
| `analysis-logic.md` | `docs/analysis-logic.md` | pi-analyze 감지 패턴, 메트릭 계산, before/after 기준 레퍼런스 |
| `baseline-v1-report.md` | `reports/baseline-v1-report.md` | v1 베이스라인 성능 리포트 |
| `v1-vs-v2-report.md` | `reports/v1-vs-v2-report.md` | v1 vs v2 비교 리포트 |

하위 에이전트(planner, worker, scout)는 pi-subagents 빌트인을 그대로 사용합니다. 행동 지시는 SKILL.md의 task string에서, `context: "fresh"`는 체인 호출에서 지정합니다. 별도 에이전트 오버라이드 파일이나 설정 파일은 필요 없습니다.

## Install

```bash
./scripts/pi-install
```

SKILL.md 심볼릭을 `~/.pi/agent/skills/giver/SKILL.md`에 생성합니다. 하위 에이전트는 `context: "fresh"` 체인 호출로 fresh 컨텍스트를 받습니다 — 전역 설정 변경 없음.

## Analyze

```bash
python3 scripts/pi-analyze              # 최신 프로젝트 세션
python3 scripts/pi-analyze --all        # 모든 세션
python3 scripts/pi-analyze --project giver-architecture
python3 scripts/pi-analyze --json       # JSON 출력
```

pi-subagents 세션 로그와 서브에이전트 아티팩트를 분석합니다: 세션 턴/토큰, 서브에이전트 타입별 분석(planner/scout/worker), 토큰 분포, Giver 프로토콜 준수(페이즈, giving of pain, 브랜치, 에러 분류, 자기 점검).

## 버전 히스토리

| 버전 | 날짜 | 변경 |
|------|------|------|
| v0 | 2026-05-19 | 초기 프로토콜 |
| v1 | 2026-05-19 | 토큰 효율 분석 기반 베이스라인 확립 |
| v2 | 2026-05-19 | `context:"fresh"` 절대 규칙, fork 금지, 타겟팅 스카웃, 태스크 분할, 체인당 Worker 1개, 브랜치 유연성 |
| v2.1 | 2026-05-20 | 버그픽스/트러블슈팅 협업 진단 규칙 — Planner가 원인 진단과 해결 선택을 독자적으로 하지 못하고, Giver가 사용자와 함께 분석한 후 구현만 위임 |

## License

MIT