# Giver 대원칙 v3.5

## 기호 ↔ 자연어 대조표

| 기호 | 자연어 |
|------|--------|
| T_0 | Task #0 (Giver가 작성) |
| T_k | Task #k (Planner가 Worker별로 큐레이팅, task{k}.md에 저장) |
| D | Dependency = (시그니처, 파일경로) 튜플 |
| R | Result = 상태 + 메시지 + Files created/modified + 새의존성 |

## 시그니처

| 역할 | 시그니처 | SCOPE |
|------|----------|-------|
| G | `user_input → T_0` | 대화 주체, 파일 수정 안 함 |
| P | `T_0 → task1.md, task2.md, ... + plan.md` | Read NO files. T_0에서만 큐레이팅 |
| S | `target_dirs → recon_data` | (Recon only) 지정된 디렉토리만 탐색 |
| W | `task{k}.md + {previous} → RESULT` | Target Files + Imports needed만 읽음 |

## 데이터 구조

| 요소 | 정의 | 비고 |
|------|------|------|
| T_0 | Goal + Background + Past failures + Constraints + Imports needed | Giver 작성 |
| T_k | Goal + Background + Past failures + Constraints + Target Files + Imports needed | Planner가 Worker별 큐레이팅, task{k}.md에 저장 |
| Dependency | (시그니처, 파일경로) | 튜플 |
| Target Files | 타겟 파일 목록 | Worker당 최대 3개 |
| Result | 상태 + 메시지 + Files created/modified + Imports needed | 성공/실패 |

## 대원칙

1. **Giver는 대화 주체** — 사용자와 대화, 결정, T_0 작성
2. **T_0만 하류로 전달** — 대화 전체가 아닌 결정사항만
3. **모든 서브에이전트는 fresh** — `context: fresh` 필수
4. **Planner는 파일을 읽지 않음** — T_0에 모든 정보 포함, 큐레이팅만 수행
5. **Planner가 task{k}.md 분리 작성** — 각 Worker는 자기 태스크만 읽음
6. **Planner가 효율적으로 큐레이팅** — Constraints에 충분한 컨텍스트를 포함하여 Worker가 추가 파일을 읽지 않도록
7. **Target Files는 Worker당 최대 3개**
8. **Imports needed는 Planner가 Worker별 큐레이팅** — T_0에서 해당 Worker가 임포트하는 것만
9. **Dependency = (시그니처, 파일경로)** — "see xxx.ts" 금지
10. **Result.상태=실패이면 즉시 중단** — 실패 시 Giver에게 리턴
11. **Past failures에 실패 이력 누적** — 재시도 시 이전 실패 포함
12. **Giver는 소스 코드 변경 시 항상 체인(Worker)을 통해** — Giver 자체는 파일 수정 안 함
13. **Worker는 {previous}로 이전 결과만 받음** — 전체 플랜이 아닌 RESULT만 누적
14. **Scout은 Phase 1.5 Recon에서만 호출** — 체인 내에 Scout 없음

## 파이프라인

```
Giver → Scout (Phase 1.5 Recon only)
Giver → T_0 → Chain:
    Planner → task1.md, task2.md, ... + plan.md (brief)
    Worker 1 ← task1.md → RESULT #0
    Worker 2 ← task2.md + {previous} → RESULT #1
    Worker N ← task{N}.md + {previous} → RESULT #N-1
```

### Planner의 역할

- T_0를 받아 Worker별 task{k}.md로 큐레이팅
- 각 Worker에 필요한 정보만 포함 (Goal, Background, Past failures, Constraints, Target Files, Imports needed)
- plan.md에 간단한 개요 작성
- 파일을 읽지 않음 — T_0에 모든 정보가 있어야 함
- 효율적으로 큐레이팅 — Worker가 추가 파일을 읽지 않도록 Constraints에 충분한 컨텍스트 포함

### Worker의 역할

- 자기 task{k}.md만 읽음
- {previous}로 이전 Worker의 RESULT를 받음
- Target Files와 Imports needed에 명시된 파일만 읽음
- 테스트 파일은 읽지 않음 — 기대값은 Constraints에 포함
- RESULT: 상태 + Files created/modified + Imports needed

## H 문서 형식

`----` 구분자. `#` 은 Task/Result에만. `##` 은 PLAN/Imports needed에.

```markdown
----
# Task #0 (for Planner)

### Goal
한 문장 목표

### Background
결정사항만

### Past failures
None — first attempt

### Constraints
기술적 제약, 테스트 기대값

### Imports needed
의존성 시그니처 + 파일경로

----
# RESULT #0 (by Worker 1)

All tests pass.
## Files created
- src/foo.ts

## Files modified
- (none)

## Imports needed (new signatures)
export function fName(params): RetType — path/to/file.ts
```

## SCOPE 규칙

| 에이전트 | 제한 |
|----------|------|
| Planner | Read NO source/test files. T_0에 모든 정보 포함. 프로젝트 루트 내만. |
| Worker | Target Files + Imports needed에 명시된 파일만. 테스트 파일 읽기 금지. |
| Scout | (Recon only) 지정된 디렉토리 내만. 프로젝트 루트 내만. |

## Do-When 패턴

모든 규칙은 긍정적 조건문으로 표현:

- ✅ "Do read only files listed in Target Files and Imports needed"
- ✅ "Do curate for efficiency — include enough context so Workers don't need to read extra files"
- ✅ "Do fill in as many Imports needed signatures as the recon provides"
- ❌ "Don't read test files" (금지문 대신 Constraints에 기대값 포함)