# Giver 원칙 v3.5.3

## 기호 정의

| 기호 | 정의 |
|------|------|
| T_0 | Task #0 — Giver가 작성하는 최초 태스크 |
| T_k | Task #k — Planner가 Worker k번을 위해 큐레이팅한 태스크 |
| D | Dependency = (시그니처, 파일경로) 튜플 |
| R | Result = Files + Signatures + Summary |

## 연산자 정의

| 역할 | 시그니처 | 정의 |
|------|----------|------|
| G | `user_input → T_0` | 사용자 대화 → 결정만 추출 |
| P | `T_0 → {T_1, T_2, ..., T_n}` | T_0에서 Worker별 태스크로 분해 |
| S | `dirs → recon` | 지정된 디렉토리 → 시그니처 + 구조 |
| W | `T_k × prev(R) → R` | 자기 태스크 × 이전 결과 → RESULT |

## 데이터 구조

```
T_0 = Goal + Background + Past failures + Constraints + Imports needed
T_k = Goal + Background + Past failures + Constraints + Target Files + Imports needed + File Relationships
D   = (시그니처, 파일경로)
R   = Files + Signatures + Summary
```

## 불변량

1. **Giver는 대화 주체** — T_0만 작성, 소스 코드 변경 안 함
2. **T_0만 하류로 전달** — 대화 전체가 아닌 결정사항만
3. **모든 서브에이전트는 fresh** — 부모 컨텍스트 누수 없음
4. **P는 T_0에서만 큐레이팅** — 소스/테스트 파일 읽기 금지
5. **P는 Worker별로 T_k를 분리 작성** — 각 Worker는 자기 T_k만 수신
6. **W는 T_k × prev(R)만 수신** — 다른 Worker의 태스크/코드에 노출 안 됨
7. **prev(R)은 이전 단계의 출력만** — 누적이 아님
8. **W의 R은 Files + Signatures + Summary만** — 코드 본문 포함 안 함
9. **D = (시그니처, 파일경로)** — 경로 없는 시그니처 금지
10. **R.상태=실패 → 즉시 중단** — Giver에게 리턴
11. **Target Files ≤ 3 per W** — Worker당 최대 3개
12. **S는 Phase 1.5 Recon에서만 호출** — 체인 내에 Scout 없음

## 파이프라인 도식

```
G → S(Recon) → G → T_0 → P → {T_1, T_2, ..., T_n}
                                     ↓
                                W_1(T_1) → R_0
                                     ↓ prev(R_0)만
                                W_2(T_2) → R_1
                                     ↓ prev(R_1)만
                                W_n(T_n) → R_{n-1}
```
