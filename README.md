# The Giver 아키텍처

> [!IMPORTANT]
> **시스템 요구사항:** pi-agent ≥ 0.74.0 및 pi-subagents ≥ 0.24.3

## 메타포: 기억의 선택적 전달

| 《기억 전달자》(소설) | The Giver (아키텍처) |
|---|---|
| 기억 전달자가 모든 기억을 통제 | **Giver**가 대화의 모든 컨텍스트를 독점 보유 |
| 수령자는 제한된 정보만 수신 | **Planner**는 Giver가 요약한 6섹션 브리프만 수신 |
| 공동체는 Sameness에 거주 | **Worker/Scout**는 이전 이력이 없는 Fresh 상태로 실행 |
| 선택적이고 의도적인 전달 | 6섹션 계약 형태로만 정보 전달(**giving**) |
| 고통의 전달 (giving of pain) | 실패 이력을 Planner에게 전달 → Planner가 Pitfalls로 번역 → Worker에게 주입 |
| Stirrings 감시 및 억제 | 실행 전후 컨텍스트 오염 검증 → Fresh 상태 보장 |

## 3-Tier 구조

```
┌─────────────────────────────────────────┐
│  🏢 Giver (Context Keeper)              │
│  전체 대화 기록 보유, 전략적 결정        │
│  하위 계층에 6섹션 브리프(~5-15K)만 전달 │
│  토큰: 선형 증가 → 주기적 압축 → 수렴   │
└──────────┬──────────────────────────────┘
           │ fresh
    ┌──────┴──────┐
    ▼             ▼
┌────────┐  ┌────────┐
│Planner │  │ Scout  │
│계획수립│  │코드정찰│
│≤500K   │  │≤100K  │
└───┬────┘  └────────┘
    │ plan.md
    ▼
┌────────┐
│ Worker │
│코드구현│
│≤80K 🟢 │
└────────┘
```

## 체인 템플릿

```
Chain 1 → [scout, planner, scout, worker]   항상 (파일 모름 → Scout가 탐색)
Chain N → [planner, scout, worker]          항상 (이전 체인 결과로 DI 앎)
Analysis → [planner]                         코드 변경 없음
```

판단 없음. 체인 번호만으로 구조 결정.

## 실패 시 Failover

| 실패 유형 | 대응 | Otherwise |
|-----------|------|-----------|
| Planner 오계획 | 재실행 + giving of pain | 3회 동일 실패 → 사용자에게 |
| Planner 과다 읽기 | 재실행 + Read ONLY | 여전하면 DI 추가 |
| Scout 연결 오류 | 재시도 1회 | Giver가 Scout 데이터 제공 |
| Worker 연결 오류 | 재시도 1회 | Worker-only (DI+SCOPE) |
| Worker 과다 읽기 | 재실행 + 강화 DI | split |
| Worker 범위 이탈 | 재실행 + 좁힌 Scope | split |

## 성능 검증

### 통제 실험: 모놀리식 vs Giver (동일 과제, 113 테스트)

| 버전 | 총 토큰 | vs 모놀리식 | 이상적(≤80K) | 낭비율 | 최대 Worker | 체인 준수 |
|------|--------:|:-----------:|:----------:|-------:|:----------:|:---------:|
| 모놀리식 | 857K 🔴 | — | 0% | 91% | 857K 🔴 | — |
| v2.4 | 640K 🟠 | +25% | 78% | 34% | 208K 🟠 | ✅ |
| **v2.5b** | **381K 🟡** | **+56%** | **88%** | **6%** | **103K 🟡** | ⚠️ 2/3 |
| v2.5a* | 290K | +66% | 33% | 25% | 144K 🟡 | ❌ Worker-only |

*v2.5a는 규칙 위반(Worker-only)으로 얻은 결과. 준수율 낮지만 토큰 절감 큼 → DI/SCOPE의 효과 증명.

### v2.5b 체인별 상세

| 체인 | 구조 | Scout | Planner | Worker | 합계 |
|------|------|------:|--------:|-------:|-----:|
| 1 | S→P→S→W ✅ | 63K 🟢 | 46K 🟢 | 42K 🟢 | 155K |
| 2 | S→P→W | 6K 🟢 | 45K 🟢 | 103K 🟡 | 154K |
| 3 | P→W ⚠️ | — | 35K 🟢 | 37K 🟢 | 73K |

Chain 3: P→W 위반이나 Worker 37K 🟢 → DI+SCOPE가 Scout를 대체한 사례. 하지만 "DI가 충분한가?"는 실행 전에 알 수 없으므로 v2.5c에서는 항상 P→S→W 강제.

### 핵심 인사이트

| 인사이트 | 근거 |
|---------|------|
| Auto-repeat ≈ 100% 준수 | 템플릿 내 지시는 판단 없이 반복 |
| Judgment-based 0-4% 준수 | "_when needed_" 조건은 무한 후퇴 |
| Do-When > Don't | "When X→do Y" > "NEVER X" |
| DI가 Worker 과다 읽기를 방지 | v2.5b: DI 포함 모든 체인 ≤103K |
| 판단 조건은 무한 후퇴 | "DI 충분?"→"DI 출처 확실?"→"확실 여부?"→모름 |
| 구조적 조건만 검증 가능 | 체인 번호, DI 섹션 존재 여부 등 |

## 종속성

| 기능 | 제공 | 활용 방식 |
|------|------|----------|
| `context: "fresh"` | pi-subagents 체인 API | 하위 에이전트를 fresh 세션으로 실행 |
| `{previous}` | pi-subagents 체인 변수 | 이전 단계 출력값을 다음 단계 입력으로 전달 |
| `defaultReads` | pi-subagents 에이전트 설정 | planner: `context.md`, worker: `plan.md` 자동 인식 |
| `output` | pi-subagents 에이전트 설정 | planner 결과를 `plan.md`로 자동 저장 |
| `chain` / `tasks` | pi-subagents 실행 모드 | 순차 체인 / 병렬 실행 |
| `contact_supervisor` | pi-subagents 인터콤 | worker/planner가 문제 시 Giver에게 에스컬레이션 |
| builtin planner/scout/worker | pi-subagents 에이전트 | 내장 에이전트 + SKILL.md 행동 지시 |

## 파일 구성

| 파일 | 경로 | 설명 |
|------|------|------|
| SKILL.md | `.pi/agent/skills/giver/SKILL.md` | Giver 프로토콜 정의 (408줄) |
| pi-install | `scripts/pi-install` | 설치 스크립트 |
| pi-analyze | `scripts/pi-analyze` | 세션 로그 분석 툴 |
| analysis-logic.md | `docs/analysis-logic.md` | 분석 패턴 및 메트릭 로직 |
| flow-diagram.md | `docs/flow-diagram.md` | 아키텍처 흐름도 |
| history.md | `docs/history.md` | 버전별 개선 이력 |

## 설치

```bash
./scripts/pi-install
```

## 분석

```bash
python3 scripts/pi-analyze              # 최신 프로젝트 세션 분석
python3 scripts/pi-analyze --all        # 전체 세션 분석
python3 scripts/pi-analyze --json       # JSON 출력
```

## License

MIT