# Giver 대원칙

## 기호 ↔ 자연어 대조표

| 기호 | 자연어 |
|------|--------|
| T | Task |
| T_0 | Task #0 (G가 작성) |
| T_k | Task #k (P가 Worker별로 큐레이팅) |
| O | Objective |
| C | Context |
| F[] | Failures |
| L[] | Limits |
| D | Dependency (시그니처, 파일경로) |
| D₀ | CuratedDeps |
| TF | TargetFiles |
| R | Result |
| H | History |

## 시그니처

| 역할 | 시그니처 |
|------|----------|
| G | `user_input → History` |
| P | `History → History` |
| S | `History → History` |
| W | `History → History` |

## 데이터 구조

| 요소 | 정의 | 비고 |
|------|------|------|
| T_0 | Objective + Context + Failures + Limits + Dependencies | G가 작성 |
| T_k | Objective + Context + Failures + Limits + TargetFiles + CuratedDeps | P가 Worker별로 큐레이팅 |
| Dependency | (시그니처, 파일경로) | 튜플 |
| CuratedDeps | init Dependencies 큐레이팅 | Worker가 임포트하는 것만 |
| TargetFiles | 타겟 파일목록 | Worker당 최대 3개 |
| Result | 상태 + 메시지 + 새의존성 | 성공/실패, 자유텍스트, 새시그니처 |

## 대원칙

1. G는 전체 컨텍스트 레벨에서 사용자와 대화하는 역할을 가진다.
2. G는 작업을 지시받으면 수행에 필요한 정보만 모아서 Task를 작성한다. G는 대화 중에 Dependencies를 만들 수도 있다.
3. T_0 = Objective + Context + Failures + Limits + Dependencies (G가 작성)
4. T_k = Objective + Context + Failures + Limits + TargetFiles + CuratedDeps (P가 Worker별로 큐레이팅)
5. subagent P, S, W는 모두 **context fresh 모드**로 실행된다.
6. P는 History를 관리한다. T_0를 큐레이팅하여 각 Worker에 맞게 Objective, Context, Failures, Limits를 추린다.
7. S는 History를 입력으로 받아 의존성을 수집한다.
8. TargetFiles는 Worker당 최대 3개 파일까지.
9. CuratedDeps는 init Dependencies에서 이 Worker에 맞게 큐레이팅한 것. Worker에서 나온 새 의존성은 {previous}를 통해 자연스럽게 전달됨.
10. Dependency = (시그니처, 파일경로)
11. Result = 상태 + 메시지 + 새의존성 (상태: 성공/실패, 메시지: 자유 텍스트)
12. 체인 실행 중 History가 누적된다. 각 에이전트는 이전 출력을 받아서 자기 출력을 append 한다.
13. Result.상태=성공이면 다음 T_k를 작성하고 History에 append. Worker에서 나온 새 의존성은 큐레이팅 없이 전부 누적. init 의존성만 CuratedDeps로 큐레이팅.
14. Result.상태=실패이면 수행 중단, History를 G에게 리턴.
15. Worker들이 모두 성공하면 G에게 최종 History를 리턴.
16. G는 History를 해석해서 사용자에게 보고.

---

## 구현체

### History 문서 형식

P는 plan.md 안에 T_k(Worker용 큐레이팅)를 만들고, W는 그 T_k를 읽고 Result를 냄.

```markdown
----
Task #0 (Planner)

### Objective
...

### Context
...

### Failures
...

### Limits
...

### Dependencies
...

----
P출력
(plan.md: T_k 포함 — Worker Briefing)

----
S출력
(context.md: 리콘 — 의존성 시그니처)

----
Result #0 (Worker 1)

All tests pass.
## Dependencies (new signatures)
export class Logger { ... }
export function createLogger(module: string): Logger;

----
S출력
(2배치 리콘)

----
Result #1 (Worker 2)

All tests pass.
## Dependencies (accumulated)
...

----
...
```

### 체인 흐름

```mermaid
사용자 ↔ G (대화, 결정)
           ↓
      G → T_0 작성 + Dependencies 수집
           ↓
      History 시작
           ↓
      P (fresh)
       │
       ├→ P출력: plan.md에 T_k 포함
       ├→ S (fresh, {previous}=P출력)
       │   └→ S출력: context.md 리콘
       ├→ W (fresh, {previous}=S출력)
       │   └→ Result #0: T_k 구현 + 새의존성
       │
       ├→ ... S→W 반복 ...
       │
       ├→ Result.상태=실패 → 중단, History를 G에 리턴
       └→ 전부 성공 → History를 G에 리턴

      G → History 해석 → 사용자 보고
```

### P의 History 처리

1. Result.상태 확인 → 성공/실패 판단
2. 성공 시: Result의 새 의존성을 다음 Worker가 참조 (큐레이팅 X)
3. 성공 시: 다음 Worker 배치 실행
4. 실패 시: History를 그대로 G에게 리턴, 실행 중단
5. 전부 성공 시: 최종 History를 G에게 리턴

### Dependencies의 두 출처

- **CuratedDeps** — init Dependencies에서 P가 큐레이팅 (계획 시점에 알던 것)
- **New Dependencies** — Worker가 새로 만든 의존성 (실행 중에 생긴 것, 큐레이팅 없이 전부 누적)