# pi-analyze — 분석 로직 레퍼런스

> pi-analyze가 어떤 패턴을 감지하고, 어떤 기준으로 before/after를 나누고, 어떤 메트릭을 계산하는지의 전체 로직을 기록합니다. 스크립트 수정이나 새 버전 비교 시 이 문서를 기준으로 재사용합니다.

## 1. 세션 로그 파싱

### 입력 소스
| 소스 | 경로 | 내용 |
|------|------|------|
| 세션 로그 | `~/.pi/agent/sessions/<project>/*.jsonl` | Giver 대화 기록 (메시지, 도구 호출, 턴) |
| 서브에이전트 아티팩트 | `~/.pi/agent/sessions/<project>/subagent-artifacts/*_meta.json` | planner/scout/worker 실행 메타 (토큰, duration, exit code) |

### JSONL 엔트리 구조
```json
{"type": "session", "timestamp": "..."}
{"type": "message", "message": {"role": "assistant", "content": [...]}}
{"type": "message", "message": {"role": "user", "content": "..."}}
{"type": "model_change", ...}
{"type": "thinking_level_change", ...}
```

### 메시지 content 블록 타입
| type | 설명 | 키 |
|------|------|-----|
| `text` | 텍스트 콘텐츠 | `.text` |
| `thinking` | 내부 사고 | — |
| `toolCall` | 도구 호출 | `.name`, `.arguments` |
| `toolResult` | 도구 결과 | — |

> **주의**: 이전 버전에서는 `tool_use`/`input` 필드를 사용했으나, 실제 로그는 `toolCall`/`arguments` 구조를 사용합니다.

---

## 2. 프로토콜 감지 로직

### Phase 감지

| Phase | 감지 조건 | 거짓 양성 방지 |
|-------|----------|---------------|
| **Phase 0** (Clarification) | `## [Phase 0` 또는 `# Phase 0:` 헤더, 또는 "Phase 0" + ("clarification" \| "질문" \| "ambiguous" \| "Ambiguity") | 단순 텍스트 언급만으로는 감지하지 않음. 구조적 컨텍스트(헤더, 테이블, 글머리 기호) 필요 |
| **Phase 1** (Impact Analysis) | `## [Phase 1` 헤더, `# Phase 1:` 헤더, "Impact Analysis Report" 구문, 또는 "Intrusion" + ("Target" \| "Scope of Change" \| "Risk") | Phase 1.5와 구분 (1.5 패턴 제외) |
| **Phase 1.5** (Branch) | `## [Phase 1.5` 헤더 또는 `Phase 1.5` 명시 | Phase 1과 구분 |
| **Phase 2** (giving/6-section) | `## [Phase 2` 헤더 **또는** 6섹션 계약 감지 (`## Objective` + 2개 이상의 {Context, Previous Failures, Target Files, Constraints, Scope Boundary}) | 단순 "objective" 단어 매칭 방지 |
| **Phase 3** (giving/Transmit) | `## [Phase 3: giving...Transmit]` 명시적 헤더만. **프로젝트 로드맵 Phase 3과 구분 필수** (예: "Phase 3 — Native Main 아키텍처"는 Giver Phase 3이 아님) | 실제 위임은 서브에이전트 호출로 파악 |
| **Phase 4** (Report & Compact) | `## [Phase 4` 헤더 또는 "context compact" / "compaction" 키워드 | — |

**Phase 3 위임 감지 (텍스트 + 행위 이원화)**:
- 텍스트 감지: 명시적 `## [Phase 3: giving — Transmit]` 헤더만
- 행위 감지: 서브에이전트 chain/task/single 호출에서 planner/scout/worker 호출 카운트

### giving of pain 감지

| 패턴 | 감지 조건 | 가중치 |
|------|----------|--------|
| Attempt N | `\*{0,2}\s*attempt\s+\d+` (대소문자 무시) | +1 per match |
| 구조화된 형식 | `what happened` + `root cause` 동시 출현 | +1 |
| What to avoid | `what to avoid` + `correct direction` 동시 출현 | +1 |
| Previous Failures 섹션 | `##\s*previous\s+failures` | +1 |
| First attempt 명시 | `none\s*[-—]\s*first\s+attempt` | +1 |

### Giver 자기 점검 감지

| 패턴 | 감지 조건 |
|------|----------|
| **영어** | `was my brief sufficient`, `giver self.?reflection`, `giver brief did not specify`, `giver correction`, `my brief was (insufficient\|not sufficient\|incomplete\|ambiguous)`, `brief did not (specify\|include\|mention)` |
| **한국어** | `브리프가 (부족\|불충분\|모호)`, `내 브리프가` + `(부족\|불충분\|모호\|충분하지)` |

### Error Source 분류 감지

각 분류(Strategic/Tactical/Operational)는 해당 단어 + ("error" \| "source" \| 해당 에이전트명) 동시 출현 시 감지:

| 분류 | 추가 조건 |
|------|----------|
| Strategic | "strategic" + ("error" \| "source" \| "giver") |
| Tactical | "tactical" + ("error" \| "source" \| "planner") |
| Operational | "operational" + ("error" \| "source" \| "worker") |
| Korean | "전략적" + "전술적" 동시 출현, 또는 "오류 원인" / "에러 원인" |

### Worker Briefing 감지

| 조건 | 설명 |
|------|------|
| `Worker Briefing` 텍스트 | 명시적 섹션 헤더 |
| `### Key Decisions` + `### Pitfalls` | Worker Briefing의 두 핵심 하위 섹션 동시 출현 |
| `### 키 결정` + `### 주의 사항` | 한국어 버전 |

### Context Compaction 감지

| 조건 | 설명 |
|------|------|
| `compact` \| `compaction` \| `compress` | + ("sawtooth" \| "요약" \| "summariz" \| "compressing" \| "context") | 압축 관련 키워드 + 컨텍스트 힌트 동시 출현 |

### Branch 작업 감지

**bash 도구 호출에서 파싱** (텍스트가 아닌 실제 명령어):

| 작업 | 감지 조건 |
|------|----------|
| Branch 생성 | `git checkout -b` |
| `giver/` 브랜치 | `giver/` 가 명령어에 포함 |
| Reset | `git checkout .` |
| Stash | `git stash` (단 `stash pop`, `stash show`, `stash list` 제외) |

---

## 3. 서브에이전트 호출 파싱

### 호출 유형

| 유형 | 구조 | 감지 |
|------|------|------|
| Chain | `{"chain": [{agent, task}, ...]}` | 순차 실행 |
| Parallel | `{"tasks": [{agent, task}, ...]}` | 병렬 실행 |
| Single | `{"agent": "planner", "task": "..."}` | 단일 에이전트 호출 |
| Management | `{"action": "list\|get\|create\|..."}` | 관리 액션 (통계 제외) |

### Context 모드 추적

| 값 | 의미 | 감지 |
|------|------|------|
| `"fresh"` | 빈 세션으로 시작 (SKILL.md 권장) | 명시적 `context: "fresh"` |
| `"fork"` | 부모 컨텍스트 상속 (위험) | 명시적 `context: "fork"` |
| `""` (empty) | 기본값 — pi-subagents에서는 `fresh`로 처리 | `context` 필드 없음 또는 빈 문자열 |

**핵심**: `resolveSubagentContext()` 함수가 `""` → `fresh`로 처리하므로 기능적으로는 fresh이나, SKILL.md는 명시적 지정을 요구.

---

## 4. Before/After 경계 정의

### Giver SKILL 적용 시점

| 버전 | 경계 | 기준 |
|------|------|------|
| **v0 (Pre-Giver)** | `2026-05-19T04:51:59` 이전 | giving of pain=0, self-reflection=0, Phase 1.5 없음 |
| **v1 (Post-Giver)** | `2026-05-19T05:31:40` 이후 | giving of pain=23, self-reflection=9, Phase 0 & 1.5 등장 |

### 경계 판단 근거

```
Pre-Giver (48세션):
  - giving of pain: 0
  - Self-reflection: 0
  - Error classifications: 1
  - Worker Briefing: 0
  - giver/ branches: 0
  - Phases: phase0, phase1, phase2, phase4 (Phase 1.5 없음)

Post-Giver (4세션):
  - giving of pain: 23
  - Self-reflection: 9
  - Error classifications: 16
  - Worker Briefing: 8
  - giver/ branches: 2
  - Phases: phase0, phase1, phase1.5, phase2, phase4 (Phase 1.5 등장)
```

**SKILL.md 적용 시각 `2026-05-19T04:52`** 기준으로 분할하되, 실제 프로토콜 사용이 감지되는 첫 세션(`05:31`)부터를 Post-Giver로 처리.

---

## 5. Monolithic 비교 모델

### 가정

| 항목 | 값 | 근거 |
|------|-----|------|
| 모델 컨텍스트 한계 | 200K tokens | Claude 실제 컨텍스트 윈도우 |
| 초기 프롬프트 | 50K tokens | 시스템 프롬프트 + SKILL.md |
| 턴당 증가 | ~20K tokens | 도구 결과 포함 평균 |
| 압축 | 없음 | Monolithic은 컨텍스트를 리셋하지 않음 |

### 계산

```
Monolithic 컨텍스트(T) = min(50K + 20K × T, 200K)
Monolithic 총 입력 = Σ min(50K + 20K × T, 200K) for T = 1..N

Giver 총 입력 = 실측값 (세션 로그에서 합산)

비율 = Monolithic / Giver
```

### 실측 결과

| 모델 | 총 입력 | 턴당 평균 | 비고 |
|------|---------|----------|------|
| **Monolithic** (200K cap) | 1,454M | 200K | 누적, 압축 없음 |
| **Giver** (실측) | 620M | 85K | 톱니 패턴, fresh 리셋 |
| **Giver (개선 후 목표)** | ~150M | ~21K | fork 금지 + ctx 명시 + 스카웃 범위 제한 |
| **Giver (이상적)** | ~130M | ~18K | 모든 Worker ≤80K |

---

## 6. Worker 토큰 효율성 분류

| 카테고리 | 입력 범위 | 비율 (v1 실측) | 설명 |
|---------|----------|--------------|------|
| 🟢 이상적 | ≤80K | 19% (5/26) | 브리프 + 타겟 코드만. SKILL.md 의도대로 |
| 🟡 수용가능 | 80-200K | 8% (2/26) | 약간 과도한 코드 리딩 |
| 🟠 과다 | 200-500K | 15% (4/26) | 불필요한 파일 리딩 의심 |
| 🔴 심각과다 | >500K | 58% (15/26) | fork 누수 또는 context.md 과다 |

### 과다 원인 매핑

| 원인 | 패턴 | Worker 평균 입력 | 해결 |
|------|------|----------------|------|
| fork 컨텍스트 누수 | `"You are a delegated subagent running from a fork of the parent"` | 2.1M | `context:"fork"` 절대 금지 |
| context.md 과다 | `"[Read from: context.md, plan.md]"` | 88K-6M | Scout 리컨 범위 제한 |
| 과도한 코드 리딩 | `"## Objective"` 단독 (범위가 넓은 태스크) | 1-6M | Target Files 명확화 |

---

## 7. 출력 형식

### `--all` 모드
모든 프로젝트의 모든 세션을 분석. Before/After 분할 시 `--boundary` 옵션으로 경계 지정.

### `--project <name>` 모드
특정 프로젝트만 분석. `--project giver-architecture` → Post-Giver만.

### `--json` 모드
JSON 출력으로 raw 데이터 제공. 버전 비교 시 사용.

### 계획된 옵션
| 옵션 | 설명 | 상태 |
|------|------|------|
| `--boundary <ISO8601>` | Before/After 경계 시각 지정 | TODO |
| `--compare <baseline.json>` | 기존 베이스라인과 비교 | TODO |
| `--version` | 스크립트 버전 출력 | TODO |

---

## 8. 버전 히스토리

| 버전 | 날짜 | 변경 |
|------|------|------|
| v0.1.0 | 2025-05-19 | 초기 버전. 텍스트 매칭 기반 Phase 감지 (오탐지 다수) |
| v0.2.0 | 2025-05-19 | 전면 개선. 정규식 헤더 매칭, 도구 호출 파싱, before/after 비교, HTML 리포트 |

---

## 9. 재사용 체크리스트

새 버전 비교 시:

1. **베이스라인 저장**: `python3 scripts/pi-analyze --json --all > reports/baseline-v<N>-giver.json`
2. **세션 데이터 저장**: `reports/baseline-v<N>-sessions.json`
3. **Before/After 경계 확인**: `--boundary` 옵션 또는 코드 내 `POST_BOUNDARY` 상수 업데이트
4. **새 감지 패턴 추가 시**: 이 문서에 패턴 등록
5. **HTML 리포트 재생성**: `reports/baseline-v<N>-report.html`
6. **비교 리포트 작성**: 이전 베이스라인과 신규 데이터 대조