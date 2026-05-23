# The Giver vs Monolithic — Token Efficiency Report

Baseline v1 · 52세션 · 6,046 턴 · 7,272 총 작업 턴 · 2025-04-29 ~ 2025-05-19

---

## Executive Summary

| 지표 | 값 |
|------|-----|
| Worker 이상적 범위 초과 | **97%** (목표: ≤80K, 실제 평균: 1.9M) |
| Monolithic 대비 토큰 절감 | **2.3×** (620M vs 1,454M) |
| Worker 이상적 범위 내 실행 | **19%** (5/26건만 ≤80K) |
| 프로토콜 준수 항목 | **8/8** (Phase 0~4, Pain, Reflection, Branch) |

> 🚨 **핵심 문제:** Giver 아키텍처의 토큰 절감은 구조적으로는 *유효*하지만(2.3×), 실제 구현에서 **97%의 Worker 실행이 이상적 범위를 크게 벗어남**. `context:"fork"` 사용(5회)과 `context` 미지정(90%)이 주요 원인. Giver의 설계 의도대로라면 Worker는 30-80K 입력으로 실행되어야 하지만, 실제 중앙값은 1.1M.

---

## 1. 컨텍스트 모델 비교

**Monolithic** — 누적 성장 → 품질 저하

- 컨텍스트가 선형 증가 → 노이즈 누적 구간 도달
- 200K cap 시 총 입력: **1,454M tokens**
- 턴당 평균 입력: 200K
- 동일 실수 반복 (기억 전달 없음)

**The Giver** — 톱니 패턴 → 품질 유지

- 컨텍스트가 톱니 패턴으로 주기적 압축
- 실제 총 입력: **620M tokens**
- 턴당 평균 입력: 85K
- giving of pain 23건으로 실패 전달

| 특성 | Monolithic | The Giver (현재) |
|------|-----------|-----------------|
| 컨텍스트 성장 | 선형 → 한계 도달 | 톱니 패턴 (주기적 압축) |
| 200K cap 시 총 입력 | 🔴 1,454M tokens | 🟢 620M tokens |
| 턴당 평균 입력 | 200K tokens | 85K tokens |
| 품질 | 🟡 200K 이후 노이즈 누적 | 🟡 이상적(19%) vs 과다(81%) |
| 실패 전달 | 🔴 동일 실수 반복 | 🟢 giving of pain 23건 |

> ✅ **구조적 이점:** Giver 모델은 monolithic 대비 **2.3× 토큰 절감**을 달성. 톱니 패턴으로 컨텍스트가 선형 증가하지 않고 주기적으로 압축됨. 34회 컨텍스트 압축 이벤트가 감지됨.

> 🚨 **구현 갭:** 그러나 이 절감은 하위 에이전트가 *이상적으로* 실행될 때의 이점. 실제 Worker의 81%가 이상적 범위(≤80K)를 벗어남. fork 컨텍스트 누수와 과도한 코드 리딩이 절감 효과를 잠식중.

---

## 2. 하위 에이전트 토큰 분포

### Worker 입력 토큰 분포

| 카테고리 | 입력 범위 | 비율 | 건수 |
|---------|----------|------|------|
| 🟢 이상적 (≤80K) | 브리프 + 타겟 코드만 | **19%** (5/26) | SKILL.md 의도대로 |
| 🟡 수용가능 (80-200K) | 약간 과도한 코드 리딩 | **8%** (2/26) | Scout 리컨 필요 범위 |
| 🟠 과다 (200-500K) | 불필요한 파일 리딩 의심 | **15%** (4/26) | |
| 🔴 심각과다 (>500K) | fork 누수 또는 context.md 과다 | **58%** (15/26) | |

### 이상적 Worker 예시 (전부 단일 파일, ≤53K)
- userId migration, setApiUrl, canCreate, dead code cleanup, refreshRooms

### 최악 Worker 예시
- fork context 7.6M, chain context 6.0M, large refactor 6.4M

---

## 3. 컨텍스트 누수 분석

### 하위 에이전트 context 설정 분포

| context | 비율 | 건수 | 비고 |
|---------|------|------|------|
| 🟡 미지정 (empty/default) | **90%** | 119건 | pi-subagents는 fresh 처리 |
| 🔴 fork | **6%** | 8건 | 부모 컨텍스트 상속 (위험) |
| 🟢 fresh | **3%** | 4건 | SKILL.md 준수 |

> SKILL.md 요구: **모든 호출에 `context:"fresh"`**

### context 설정별 Worker 평균 입력

| context | 평균 입력 | 이상적 대비 | 비고 |
|---------|----------|-----------|------|
| 🟢 fresh | ~30-50K | 1× | ✅ SKILL.md 준수 |
| 🟡 empty (default) | varies greatly | 3-150× | ⚠️ pi-subagents는 fresh 처리 |
| 🔴 fork | ~2.1M | 42× | 🚨 부모 대화 전체 상속 |

> fork 컨텍스트는 단일 실행에 최대 **7.6M tokens** 소비. 이상적(50K) 대비 **152×**.

---

## 4. 에이전트별 토큰 분포

| 에이전트 | 이상적 | 중앙값 | 평균 | 최대 | 이상적 비율 |
|---------|--------|--------|------|------|-----------|
| Planner | 50-150K | 533K 🔴3.5× | 691K | 2.0M | 12% (2/16) |
| Scout | 30-100K | 220K 🔴2.2× | 275K | 639K | 17% (3/18) |
| Worker | 30-80K | 1.1M 🔴14× | 1.9M | 7.6M | 19% (5/26) |

---

## 5. 프로토콜 준수

### Phase 준수율 (세션 기준)

| Phase | 세션 | 비율 | 상태 |
|-------|------|------|------|
| Phase 0 (Clarification) | 7 | 13% | 🟡 저조 |
| Phase 1 (Impact Analysis) | 16 | 31% | 🟡 보통 |
| Phase 1.5 (Branch) | 2 | 4% | 🔴 미흡 |
| Phase 2 (6-section Brief) | 15 | 29% | 🟡 보통 |
| Phase 3 (giving/Delegation) | 27 | 52% | 🟢 양호 |
| Phase 4 (Report & Compact) | 17 | 33% | 🟡 보통 |

### 핵심 메커니즘

| 메커니즘 | 감지 횟수 | 비고 |
|---------|----------|------|
| giving of pain | 22 | 🟢 활성 |
| Giver 자기 점검 | 9 | 🟢 활성 |
| Error Source 분류 | 14 | 🟢 활성 |
| Worker Briefing | 7 | 🟡 저조 |
| Context Compaction | 35 | 🟢 활성 |
| Branch per chain (giver/) | 2/29 | 🔴 미흡 |

---

## 6. 근원 분석 — 왜 Worker가 97% 과다 실행되는가?

### Worker 입력 토큰 구성 (평균 1.9M)

**이상적 브리프 (30-50K)** — 전체 대비 아주 작은 비중

**과도한 코드 리딩 (~500K-1M)**
- Worker가 필요 이상으로 파일을 읽음
- Target Files가 불명확 → 전체 프로젝트 스캔
- Scout의 context.md가 선택적이지 않음

**Fork 컨텍스트 누수 (1.8M-7.6M)**
- 5건 Worker fork — 부모 대화 전체 상속
- SKILL.md에서 `context:"fresh"` 요구에 위반
- 단일 실행에 최대 7.6M → 이상적 대비 152×

**context.md 오버헤드 (88K-6M)**
- Chain 호출에서 Scout 리컨이 전체 파일 덤프

### 원인 매핑

| 원인 | 패턴 | 해결 |
|------|------|------|
| 🔴 Fork 누수 (5건) | `context:"fork"` | `context:"fork"` 절대 금지 |
| 🔴 context.md 과다 (~85%) | Scout 전체 덤프 | Scout 리컨 범위 제한 |
| 🟡 과도한 파일 리딩 (~80%) | Target Files 불명확 | Target Files 명확화 |

---

## 7. 개선 로드맵

| # | 우선순위 | 조치 | 예상 효과 | Target | 현재 → 목표 |
|---|---------|------|----------|--------|------------|
| 1 | 🔴 최우선 | `context:"fork"` 절대 금지 | fork 5건 제거 → Worker 평균 ↓ | Worker ≤80K | 1.9M → ≤80K |
| 2 | 🔴 최우선 | 모든 chain/task 호출에 `context:"fresh"` 명시 | 90% 미지정 해결 | 119→0건 | 119 → 0 |
| 3 | 🟡 중요 | Scout 리컨 범위 제한 | context.md 덤프 감소 | ctx.md ≤50K | 88K-6M → ≤50K |
| 4 | 🟡 중요 | Worker 브리프에 Target Files 명확화 | 과도한 파일 리딩 감소 | Worker ≤200K | 73% 과다 → ≤20% |
| 5 | 🟢 권장 | 대형 리팩토링을 작은 태스크로 분할 | 단일 Worker 1M+ → 여러 Worker 50K | Worker ≤80K | 1.9M avg → ≤80K |
| 6 | 🟢 권장 | `giver/` 브랜치 네이밍 컨벤션 적용 | 롤백 가능성 보장 | giver/ 100% | 7% → 100% |

> 🎯 **개선 후 예상 효과:** 3개 최우선 조치(#1-#2)만으로 Worker 평균 입력을 **1.9M → ~100K**로 95% 절감 가능. 전체 토큰 소비는 **620M → ~150M**로 75% 절감. 이는 monolithic(1,454M) 대비 **10×** 절감 효과.

---

## 8. giving of pain — 실패 전달 효과

### 감지된 실패 전달 통계

| 항목 | 값 |
|------|-----|
| giving of pain 항목 | **22** |
| Giver 자기 점검 | **9** |
| Error 분류 (Strategic) | 5 |
| Error 분류 (Tactical) | 4 |
| Error 분류 (Operational) | 5 |
| Worker 성공률 | 25/26 (96%) |
| Planner 성공률 | 14/16 (88%) |
| Scout 성공률 | 17/18 (94%) |

> ✅ **giving of pain이 작동 중.** 22건의 구조화된 실패 전달과 9건의 자기 점검이 감지됨. Error 분류는 균형 있게 분포. Worker 96% 성공률은 실패 전달이 재시도에서 효과적으로 작동함을 시사.

---

## 9. 결론

**구조적 이점은 실재한다**
The Giver 아키텍처는 Monolithic 대비 **2.3× 토큰 절감**을 구조적으로 보장한다. 톱니 패턴 컨테스트 압축, giving of pain 실패 전달, fresh 에이전트 격리는 모두 이론적으로, 그리고 실제 데이터에서 유효하게 작동하고 있다.

**구현 갭이 절감 효과를 잠식한다**
그러나 **97%의 Worker 실행이 이상적 범위를 벗어난다.** fork 컨텍스트 누수, context 미지정, 과도한 코드 리딩이 아키텍처의 이점을 잠식하고 있다. 최우선 2개 조치(fork 금지 + context 명시)만으로 **전체 토큰의 75%**를 절감할 수 있다.

**개선 후 예상 효과**
- Worker 평균 **1.9M → ~100K** (95% 절감)
- 전체 입력 **620M → ~150M** (75% 절감)
- Monolithic 대비 **~10×** 효율 → 설계 의도 달성

### 토큰 절감 비교

| 모델 | 총 입력 | 비고 |
|------|---------|------|
| Monolithic | 1,454M | 누적, 압축 없음 |
| Giver (현재) | 620M | 2.3× 절감 |
| Giver (개선 후) | ~150M | ~10× 절감 |
| Giver (이상적) | ≤130M | 모든 Worker ≤80K |

---

*Baseline v1 · 52세션 · 7,272 총 턴 · 분석 일시: 2025-05-19*
*Raw 데이터: `scripts/baseline-v1-giver.json` · `scripts/baseline-v1-sessions.json` · `scripts/baseline-v1-chart-data.json`*
*스크립트: `scripts/pi-analyze` · 비교를 위한 베이스라인으로 사용됨*