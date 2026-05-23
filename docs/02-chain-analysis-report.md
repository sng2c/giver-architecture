# Giver 체인 수치 분석 보고서

**분석 일시**: 2026-05-23  
**분석 대상**: 18개 체인 실행 덤프  
**분석 도구**: `scripts/analyze-chains.py`, `scripts/extract-chain.sh`

---

## 1. 개요

| 지표 | 값 |
|---|---|
| 총 체인 수 | 18 |
| 총 토큰 (input) | 61.9M |
| 총 토큰 (output) | 817K |
| Planner 성공률 | 16/17 (94%) |
| Worker 성공률 | 49/53 (92%) |

---

## 2. 핵심 발견: W/P 비율과 Worker 과다 읽기

Worker 최대 input / Planner input 비율(W/P)이 Worker 과다 읽기의 핵심 지표다. W/P가 낮을수록 Planner 큐레이션이 효과적이다.

### W/P 비율 분포

| 등급 | W/P 범위 | 체인 수 | 비고 |
|---|---|---|---|
| 🟢 효율 | < 5x | 8 | Planner 큐레이션이 충분 |
| 🟡 양호 | 5-15x | 4 | 일부 Worker 과다 읽기 |
| 🔴 비효율 | 15-50x | 2 | Worker가 Planner보다 15-50배 더 읽음 |
| 💀 치명 | > 50x | 2 | Worker가 Planner보다 50배 이상 더 읽음 |

### W/P 비율 순위

| 체인 | W/P | P_input | W_max | 등급 |
|---|---|---|---|---|
| ae971ff0 | 0.1x | 75K | 6K | 🟢 |
| dc64d963 | 0.2x | 3.6M | 547K | 🟢 |
| 2d451efc | 0.8x | 1.3M | 1.1M | 🟢 |
| a15cee3f | 0.9x | 1.8M | 1.7M | 🟢 |
| 57d29f0e | 1.4x | 101K | 139K | 🟢 |
| db552cac | 1.4x | 1.1M | 1.4M | 🟢 |
| 34e3f185 | 2.0x | 1.3M | 2.6M | 🟢 |
| 392048db | 2.0x | 1.5M | 3.1M | 🟢 |
| 64b71ad3 | 5.1x | 992K | 5.1M | 🟡 |
| 559fc35e | 9.7x | 68K | 662K | 🟡 |
| 3dd85357 | 11.1x | 61K | 677K | 🟡 |
| 1c87533c | 14.5x | 19K | 279K | 🟡 |
| a58bf658 | 16.4x | 131K | 2.2M | 🔴 |
| 6ee6a580 | 32.0x | 188K | 6.0M | 🔴 |
| cd148908 | 47.0x | 25K | 1.2M | 🔴 |
| d8087849 | **186.3x** | 19K | 3.6M | 💀 |

---

## 3. Worker 과다 읽기 원인 분석

### 원인 1: Planner 큐레이션 부족 (P_input < 100K)

P_input이 100K 미만이면 T₀가 충분하지 않아 Worker가 직접 파일을 읽어야 함.

| 체인 | P_input | W_max | W/P | 결과 |
|---|---|---|---|---|
| 2c9960b2 | 8K | 0 | — | ❌ Planner만 실행 |
| 1c87533c | 19K | 279K | 14.5x | ✅ Worker 과다 읽기 |
| d8087849 | 19K | 3.6M | **186.3x** | ❌ Worker 81턴 루프 |
| cd148908 | 25K | 1.2M | 47x | ✅ Worker 과다 읽기 |
| 3dd85357 | 61K | 677K | 11x | ✅ Worker 과다 읽기 |
| 559fc35e | 68K | 662K | 10x | ✅ Worker 과다 읽기 |
| ae971ff0 | 75K | 6K | 0.1x | ❌ Worker 거의 안 읽음 |

**P_input < 100K인 체인 7개 중 5개가 W/P > 10x.** Planner가 충분한 큐레이션을 하지 못하면 Worker가 대신 과다 읽는다.

### 원인 2: "follow existing patterns" 지시 (v3.5 이전)

v3.5 이전에는 Planner가 "follow existing patterns"만 제시. Worker가 대형 파일(5000+ 줄)을 40회 이상 반복 읽음.

| 체인 | Worker 턴 | Input/Turn | 원인 |
|---|---|---|---|
| d8087849 W1 | 81 | 44K | 5373줄 파일 반복 읽기 |
| 64b71ad3 W3 | 81 | 63K | 대형 파일 반복 읽기 |
| 6ee6a580 W2 | 64 | 94K | 대형 파일 반복 읽기 |
| 34e3f185 W2 | 42 | 63K | 대형 파일 반복 읽기 |

### 원인 3: Planner 과다 읽기 (P_input > 1M)

P_input이 과도한 경우도 있음. 이는 Planner가 소스 파일을 직접 읽었기 때문.

| 체인 | P_input | 원인 |
|---|---|---|
| dc64d963 | 3.6M | Planner가 소스 파일 직접 읽음 (v3.5 이전) |
| a15cee3f | 1.8M | Planner 과다 읽기 |
| 392048db | 1.5M | Planner 과다 읽기 |

---

## 4. Worker 최대 input 분류

| 등급 | W_max 범위 | 체인 수 | 비율 |
|---|---|---|---|
| 🟢 < 100K | 효율 | 3 | 17% |
| 🟡 100K-500K | 양호 | 2 | 11% |
| 🟠 500K-1M | 주의 | 3 | 17% |
| 🔴 1M-3M | 비효율 | 6 | 33% |
| 💀 > 3M | 치명 | 4 | 22% |

**45%의 체인이 Worker 1M+ input.** Worker 과다 읽기가 여전히 주요 문제.

---

## 5. v3.5+ 개선 효과

v3.5 (Planner 파일 읽기 금지 + RESULT 간소화) 적용 전후 비교:

| 지표 | v3.5 이전 (d8087849) | v3.5 (c2e86d3b) | v3.5.13 (dc64d963) |
|---|---|---|---|
| P_input | 19K | 30K | 3.6M* |
| W_total | 3.6M | 368K | 595K |
| W/P | 186x | 6.1x | 0.2x* |
| Worker 턴 | 81 | 8 | 27 |
| 테스트 | ❌ | 44/44 ✅ | ✅ |

*: dc64d963는 Planner가 읽기를 허용받은 v3.5.12+ 체인. P_input이 높지만 Worker는 효율적.

---

## 6. 결론 및 v3.5.13 개선 방향

### 핵심 인사이트

1. **P_input < 100K → W/P > 10x (71%)**: Planner 큐레이션이 충분하지 않으면 Worker가 과다 읽음
2. **"follow existing patterns" → Worker 40-81턴 루프**: 패턴을 인라인 제공하면 1-8턴으로 감소
3. **Planner 1M+ 읽기 → W/P < 2x**: Planner가 충분히 읽으면 Worker는 효율적

### v3.5.13 개선 기대

| 개선 | 메커니즘 | 기대 효과 |
|---|---|---|
| Signatures 통합 | Imports needed → Signatures | T₀/Tₖ 일관성, 큐레이션 명확화 |
| Breaking forward | Worker가 이전 Breaking 전달 | "edit→fail→re-read" 루프 방지 |
| T₀ Target Files 추가 | Planner가 T₀에서 Target Files 참조 | Planner 읽기 범위 명확화 |
| Planner 읽기 허용 | Planner가 Target Files에서 패턴 추출 | Worker 과다 읽기 감소 |
| reads:false 설명 보강 | defaultReads 방지, read 도구는 사용 가능 | 혼란 방지 |

### 예상 효과

- **W/P < 15x 체인**: 44% → 80%+ (Planner 큐레이션 개선)
- **Worker 1M+ input**: 55% → 20% (패턴 인라인 + Breaking forward)
- **Worker 과다 턴 (>40)**: 4건 → 0-1건 (패턴 제공으로 1-8턴 예상)
