# pi-the-giver

[![npm version](https://img.shields.io/npm/v/@sng2c/pi-the-giver?style=flat-square)](https://www.npmjs.com/package/@sng2c/pi-the-giver) [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](https://opensource.org/licenses/MIT)

> *"전달받을 거라면, 온전한 기억이어야 해."*
> — 로이스 로리, 《기억 전달자(The Giver)》

Pi 코딩 에이전트용 스킬. 코딩 과제를 **Planner + N Workers** 파이프라인으로 위임하며, **엄격한 컨텍스트 격리**를 보장한다. 당신은 **Giver**와 대화하고, Giver는 위임한다. Giver는 코드를 직접 고치지 않는다 — 모든 대화 컨텍스트를 품은 기억 전달자가, 그것을 증류하여 task 브리프로 만들어 fresh하고 스코프가 제한된 Worker들에게 건넬 뿐.

## 설치

```bash
pi install npm:@sng2c/pi-the-giver
```

## 활성화

```
/skill:giver
```

또는 프로젝트 지시 파일(`.pi/AGENTS.md`)에 추가해 코딩 과제에 자동 활성화.

## 빠른 시작

```
Use the giver skill to implement a user authentication module with login, signup, and password reset
```

Giver가 Planner → Workers 파이프라인을 돌린다 — Task #0 작성, 단독 Planner로 정확한 Worker 수 N 산출, N개 Worker의 foreground 체인 구성·실행, 검증·보고.

---

## 은유 — 왜 "The Giver"인가

로이스 로리의 《기억 전달자》에서 **기억 전달자(Receiver of Memory)** 한 사람이 세상의 모든 기억을 품는다. 나머지는 **Sameness** 속에 산다 — 역사도, 맥락도, 축적된 노이즈도 없이. 기억 전달자는 필요한 순간에 필요한 기억만 골라 전달한다. **고통의 전달(giving of pain)** — 레거시의 고통스러운 진실, 실패, 제약, 절대 다시는 반복하지 말아야 할 것 — 은 정제되어 백지 상태의 수령자에게 주입된다.

이 스킬은 소설 그 자체를 코딩 에이전트에 옮긴 것이다:

| 소설 | Giver 스킬 |
|---|---|
| 전달자가 모든 기억을 품는다 | Giver가 모든 대화 컨텍스트를 품는다 |
| 공동체는 Sameness 속에 산다 | Worker·Scout는 **fresh**로 실행 — 히스토리 0 |
| 전달자는 선택된 기억만 전달 | Planner/Worker는 T₀ / task 파일만 수신 |
| 고통의 전달 — 실패·제약·금기 | `Past failures` + `Constraints`를 T₀에 주입 |
| 기억은 아래로 누수되지 않는다 | Giver의 대화는 에이전트 경계를 넘지 않는다 |
| 전달자는 전달만, 세상을 고치지 않는다 | Giver는 위임만, 코드를 직접 고치지 않는다 |

아키텍처는 스킬 위에 얹은 장식이 아니다 — **스킬이 곧 은유**다. Giver는 기억 전달자이고, 모든 하류 에이전트는 증류된 핵심만 받는 백지 수령자다.

---

## 왜 효율적인가 — 컨텍스트 격리 + 관심의 분리

코딩 에이전트는 매 단계에서 파일을 읽고, 코드를 쓰고, 테스트를 돌린다. 이 **코딩 I/O**(소스·테스트 출력·에러 로그)가 누적되며 컨텍스트는 지수적으로 팽창한다:

$$
|\text{context}(n)| = |\text{context}(1)| \cdot r^{n-1} \quad (r > 1)
$$

컨텍스트가 커질수록 **스티어링**(방향 지시: "이 파일 만들어", "저 에러 고쳐", "Z일 때만 Y 접근 써")이 코딩 I/O 노이즈에 잠긴다. 에이전트는 방향을 잃는다 — 잘못된 파일을 고치고, 이미 고친 에러를 재시도하고, 목표에서 표류한다.

Giver는 직교하는 두 축으로 이 문제를 공격한다.

### 축 1 — 컨텍스트 격리 (에이전트 경계 너머)

컨텍스트를 **스티어링**(방향 지시)과 **코딩 I/O**(실행 산물)로 분해한다. **에이전트 경계를 넘는 건 스티어링뿐.** 코딩 I/O는 그것을 만든 에이전트 안에 머문다.

- Giver의 전체 대화(~500K 토큰의 결정·대화·버린 시도)는 Worker에 닿지 않는다.
- 각 Worker는 **fresh**로 실행되며, 작은 `RESULT`(`Files / Signatures / Breaking / Summary`, 코드 본문·테스트 출력 없음)만 내놓는다.
- 다음 Worker는 형제들의 전체 실행 궤적이 아니라, **구조적 주입**(프레임워크의 `results.md` `[Read from:]` prefix)으로 이전 `RESULT`를 받는다.

| 경계 | 넘는 것(스티어링) | 격리(코딩 I/O) | 격리율 |
|---|---|---|---|
| G → P | T₀ | Giver 대화 | ~99% |
| P → Wₖ | taskₖ.md | 다른 Worker 태스크 | 83–93% |
| Wₖ → G | RESULT | Worker 실행 전체 | 98–99% |

> 격리율 = 1 − (전달 크기 / 격리 전 컨텍스트 크기).

### 축 2 — 관심의 분리 (파이프라인 내부)

각 역할은 정확히 하나의 관심을 소유하고, 다른 이의 I/O를 담지 않는다:

| 역할 | 컨텍스트 | 소유 | 하지 않는 것 |
|---|---|---|---|
| **Giver** | 대화 | 결정 → T₀ | 코드 수정 |
| **Planner** | fresh | task 파일 + 정확한 N + 레이어 순서 큐레이팅 | 구현 |
| **Scout** | fresh | 정찰 → 시그니처 | 구현 |
| **Worker** | fresh | 자기 스코프 파일 + 자가 검증 | 다른 스코프 건드림 |

관심이 분리되어 한 Worker의 컨텍스트에 다른 에이전트의 결정이나 실행이 섞이지 않는다. 에이전트가 격리되어 파이프라인 전체 컨텍스트는 **가산적**(작은 fresh 컨텍스트들의 합)으로 자라지, **지수적**(하나의 눈덩이 전사)으로 자라지 않는다.

### 구조, 지시가 아니라

results.md는 프레임워크의 `[Read from: <chainDir>/results.md]` prefix로 하류 Worker에게 흐른다 — Worker에게 "출력을 전달해 달라"고 부탁해서가 아니다. 파이프라인의 정확성이 에이전트가 prose를 성실하게 에코하는지에 의존하지 않는다. **지시보다 구조**: 에이전트가 정중하든 아니든 메커니즘은 작동한다.

---

## 파이프라인

```
요청 → Giver(논의/결정) → T₀ → Planner(단독, fresh) → Plan(정확한 N + task 파일)
                                            ↓
                     Giver가 foreground W×N 체인 구성
                                            ↓
   W₁ (task1.md 읽기)                → RESULT #1 → results.md
   W₂ (task2.md + results.md 읽기)   → RESULT #2 → results.md
   …                                  …
   W_N                                → RESULT #N → results.md   → 체인 자연 종료
                                            ↓
                     Giver가 results.md 읽고 검증·보고
```

- **Scout**는 시그니처/타깃 파일 정찰이 필요할 때 Giver가 체인 전에 단독 호출.
- **Planner**는 단독(체인 밖)으로 돌아 **정확한 N** + 의존성 레이어 순서를 반환 → 체인이 정확히 사이징됨(빈 슬롯 없음).
- **Worker**는 단일 foreground 체인 안에서 fresh로 실행되며, 각자 task 파일과 누적 `results.md`만 받는다.

## 왜 순차 파이프라인인가 (병렬이 아닌)

Worker는 **W₁ → W₂ → … → W_N 순서**로 실행되며, 동시에 돌지 않는다. 이유는 **변경의 영향 반영**: 한 Worker의 편집이 다음 Worker가 빌드해야 할 실제 상태를 바꾸기 때문이다.

- **같은 파일, 여러 관심**: W₁은 `UserService` 추가, W₂는 그것을 import하는 `UserController` 추가, W₃은 테스트 추가 — 셋 다 `user.ts`를 건드린다. W₂는 W₁이 *쓴 뒤의* `user.ts`를 읽어야 하고, W₃은 둘 다 쓴 뒤의 것을 읽어야 한다. 병렬이면 각 Worker가 정적 스냅샷에 고정되어 공유 파일에서 충돌한다.
- **익스포트 의존**: Layer 0가 심볼 생성, Layer 1가 import, Layer 2가 테스트. Wₖ의 task는 W_{k-1}이 실행된 뒤에야 존재하는 시그니처를 참조한다. `results.md`가 실제 `Signatures`/`Breaking`을 앞으로 전달하여 Wₖ가 가정이 아닌 **실제 익스포트** 위에서 빌드한다.
- **Breaking 가드레일**: Wₖ가 익스포트를 제거/개명하면, W_{k+1}는 시작 *전*에 `results.md`에서 그 사실을 본다 — 파일을 읽고 옛 심볼을 못 찾아 루프도는("edit → fail → re-read" 함정) 대신.

병렬은 파일을 **겹침 0**, **Worker 간 의존 0**으로 미리 분할해야 한다 — 독립 청크에만 가능하고 취약(공유 파일 하나나 import 하나만 끊어져도 깨짐). 순차 실행은 Giver의 분해 자유를 지킨다: *논리적 수정 그룹*으로 쪼개고, 그룹이 파일을 공유하고 서로 의존하게 두고, 각 Worker가 **진짜 변경 후 상태** 위에서 빌드하게 한다. 그 비용(직렬 지연)은 공유 상태 아래 정확성의 대가이며, 체인의 구조적 `[Read from: results.md]` 주입이 그 전달을 prose 지시 없이 신뢰 가능하게 만든다.

## 왜 completionGuard가 없는가

초기 버전(v3.7.5)은 10개 고정 Worker 슬롯을 미리 깔고, 미사용 꼬리를 pi-subagents의 `completionGuard`로 끊었다(no-op Worker가 아무것도 안 쓰면 → 체인이 에러로 완료 시그널). 이 우회는 Planner가 **체인 안**에 있어 N을 실행 도중에 결정할 수밖에 없어, 슬롯을 미리 깔아야 했기 때문에 생겼다.

v0.1.0은 Planner를 **단독**으로 빼서, N을 체인 빌드 *전*에 확정한다. Giver는 **정확히 N**개 Worker 체인을 구성한다 — 빈 슬롯 0, no-op 0, `[CHAIN COMPLETED]` 0, `completionGuard` 재용 0. 체인은 W_N 뒤 자연 종료한다. (`append-step`/async는 e2e 테스트 후 기각 — `docs/history.md` 참고.)

## 의존성

[pi-subagents](https://www.npmjs.com/package/pi-subagents) `latest` 필요 (foreground 체인 + 구조적 `[Read from:]` reads 주입).

## 참조

| 파일 | 내용 |
|---|---|
| [skills/giver/SKILL.md](skills/giver/SKILL.md) | 전체 구현 — Phase, 템플릿, RESULT 포맷, 실패 프로토콜 |
| [giver-principles.md](giver-principles.md) | 수학적 정의 — 6원리, 집합, 함수, 불변량 |
| [docs/insights.md](docs/insights.md) | v1~v3.7.x 진화에서 얻은 인사이트 |
| [docs/history.md](docs/history.md) | 버전·설계 이력 (v1 → v0.1.0, append-step → Pattern C 테스트 여정 포함) |

## 버전 히스토리 (요약)

| 버전 | 날짜 | 변경 |
|---|---|---|
| v3.0 | 2026-05 | 초기 Planner → Workers 파이프라인 |
| v3.6.3 | 2026-05 | Target 검증 스코프 (검증 I/O −81%) |
| v3.7.0 | 2026-05 | results.md 구조적 통신 |
| v3.7.5 | 2026-05 | 고정 10슬롯 + completionGuard 우회 |
| v3.8.0 | 2026-07 | Pattern C — foreground W×N, 단독 Planner의 정확한 N (e2e 테스트) |
| **v0.1.0** | 2026-07 | 패키지 리네임 `@sng2c/giver-skill` → `@sng2c/pi-the-giver`; 버전 리셋. 아키텍처 = Pattern C (v3.8.0 설계) |

## 라이선스

MIT