# Giver

v3.5.6

## Giver란

사용자의 코딩 작업을 대화로 받아, 여러 에이전트에 작업을 나누어 위임하는 오케스트레이터다. 사용자는 Giver와 대화하고, Giver는 체인을 통해 Planner·Scout·Worker를 호출한다.

## 문제: 코딩 I/O의 누적

코딩 에이전트는 파일을 읽고, 코드를 작성하고, 테스트를 돌린다. 이 **코딩 I/O**(소스 파일, 테스트 출력, 에러 로그)가 스텝마다 누적되면 컨텍스트가 지수적으로 증가한다.

$$
|\text{context}(n)| = |\text{context}(1)| \cdot r^{n-1} \quad (r > 1)
$$

컨텍스트가 커지면 **스티어링**(방향 지시: "어떤 파일을 만들지, 어떤 에러를 고칠지")이 코딩 I/O 노이즈에 묻힌다. 결과적으로 에이전트가 엉뚱한 파일을 수정하거나 이미 고친 에러를 재시도하는 등 방향을 잃는다.

## 해법: 스티어링 격리 파이프라인

컨텍스트를 **스티어링**(방향 지시)과 **코딩 I/O**(실행 산출물)로 분해하고, 에이전트 경계에서 스티어링만 전달한다.

```mermaid
graph LR
    G["Giver"] -->|Recon| S["Scout"]
    S -->|시그니처| G
    G -->|"T₀"| P["Planner"]
    P -->|task| W1["Worker 1"]
    W1 -->|R₁| W2["Worker 2"]
    W2 -->|R₂| W3["Worker 3"]
    W3 -->|R₃| W4["..."]
```
Giver는 항상 P→W×10 체인을 시작한다. Planner가 task 수(N ≤ 10)를 결정하면, task 파일이 없는 Worker 슬롯은 no-op로 즉시 종료된다. 같은 파일을 여러 Worker가 순차 수정 가능.

| 경계 | 전달 (스티어링) | 격리 (코딩 I/O) | 격리율 |
|------|--------------|---------------|--------|
| G → P | T₀ | Giver 대화 (~500K토큰) | **99%** |
| P → Wₖ | taskₖ.md | 다른 Worker 태스크 | **83~93%** |
| Wₖ → G | RESULT | Worker 실행 전체 | **98~99%** |

> 격리율 = 1 − (전달 크기 / 격리 전 컨텍스트 크기). 출처: c2e86d3b 체인 측정

## 3-tier 구조

**Giver**(대화): 사용자 대화에서 결정을 추출하여 T₀를 작성. 코드를 직접 다루지 않음.

**Planner**(계획): T₀에서 Worker별 task{k}.md를 생성. 소스/테스트 파일은 읽지 않음 — T₀에 필요한 정보가 모두 들어 있음.

**Worker**(실행): 자기 task{k}.md와 이전 Worker의 RESULT만 수신. 격리된 스코프에서 작업을 실행. 각 Worker는 fresh 컨텍스트로 실행되어 부모나 다른 Worker의 I/O에 영향을 받지 않음.

## 파이프라인

```
G → S(Recon) → G → T₀ → P → {T₁, T₂, T₃}
                                ↓
                           W₁(T₁) → R₁
                           W₂(T₂, R₁) → R₂       ← R₂는 R₁을 반영 (조합 전이)
                           W₃(T₃, R₂) → R₃       ← R₃는 R₁, R₂를 반영
```

- **Scout**: Giver가 코드 구조를 직접 읽지 않고 Scout에게 위임. 체인 밖에서만 호출.
- **RESULT = Files + Signatures + Summary**: 코드 본문은 포함하지 않아 {previous}를 통한 I/O 역류를 차단.
- **조합 전이**: Rₖ는 Rₖ₋₁의 결과를 반영하여 만들어지므로 정보가 조합적으로 하류에 전달됨. 하지만 각 RESULT는 스티어링만 포함하므로 |Rₖ|는 일정 범위에 바운드됨.

> Phase 정의, SCOPE 규칙, 템플릿, 실패 프로토콜은 [SKILL.md](.pi/agent/skills/giver/SKILL.md) 참조

## 성능

> redbis-coding-test 프로젝트(44 tests), c2e86d3b 체인. 토큰 사용량(input).

| 구조 | Planner | Worker 1 | Worker 2 | Worker 3 | **Total** |
|------|---------|----------|----------|----------|-----------|
| Monolithic | — | — | — | — | **864K** |
| v3.5 | 30K | 68K | 86K | 184K | **368K** |

- Monolithic: 단일 에이전트가 전체 작업을 실행. 비교 기준.
- v3.5: 스티어링 격리 파이프라인으로 동일 작업 실행. Total 58% 감소.

## 참조

| 파일 | 내용 |
|------|------|
| [SKILL.md](.pi/agent/skills/giver/SKILL.md) | 전체 구현 (Phase, 템플릿, SCOPE, H 문서, 실패 프로토콜) |
| [giver-principles.md](giver-principles.md) | 수학적 정의 (6원리, 집합, 함수, 불변량) |
| [analysis-logic.md](docs/analysis-logic.md) | 분석 로직 및 도구 사용법 |
| [history.md](docs/history.md) | v1~v2.5i 개선 이력 |

## 버전 히스토리

| 버전 | 날짜 | 변경 |
|------|------|------|
| v3.0 | 2025-05 | 초기 파이프라인 아키텍처 |
| v3.2 | 2025-05 | 체인 내 Scout 제거, Planner가 Imports needed 큐레이팅 |
| v3.3 | 2025-05 | Planner가 task{k}.md 분리 작성 |
| v3.5 | 2025-05 | Planner "T₀에서만 큐레이팅", RESULT = Files/Signatures/Summary |
| v3.5.6 | 2025-05 | 논리적 수정 그룹 기준, 같은 파일 순차 수정 허용, P→W×10 고정 체인, no-op 슬롯 처리 |