# Giver v3.6 성능 비교 리포트

## 1. 개요

v3.6 시리즈(v3.6 ~ v3.6.2)의 핵심 변경사항과 성능 영향을 분석한다. 분석 대상은 과거 체인 아티팩트 24개(Planner 포함 21개) 기준.

## 2. 버전별 아키텍처 차이

| 항목 | v3.5 (이전) | v3.6.1 | v3.6.2 |
|------|------------|--------|--------|
| **Planner reads** | `false` | `false` | `false` |
| **Planner output** | `false` | `false` | `"plan.md"` |
| **Worker reads** | manual read | manual read | `["taskN.md"]` auto-inject |
| **Task 파일 위치** | cwd (프로젝트 루트) | cwd | chain directory |
| **Worker task 수신** | `read` 도구로 직접 읽기 | `read` 도구로 직접 읽기 | `[Read from:]` 프리픽스 자동 주입 |
| **잔여 파일 위험** | ⚠️ 과거 실행 잔여 | ⚠️ 과거 실행 잔여 | ✅ chain directory에만 존재 |
| **Design Principles** | 없음 | ✅ GGON 5원칙 | ✅ GGON 5원칙 |
| **RESULT Breaking** | 없음 | ✅ Breaking forward | ✅ Breaking forward |

## 3. 핵심 변경: Task 파일 경로 문제 해결 (v3.6.2)

### 문제

v3.6.1에서 Worker가 `reads:false` + `read` 도구로 task 파일을 읽을 때:
1. Planner가 **cwd**(프로젝트 루트)에 task 파일 작성
2. Worker가 `read` 도구로 task 파일을 cwd에서 찾음 → 작동은 하지만...
3. **과거 실행의 잔여 task 파일**을 읽을 위험 존재
4. `reads:["taskN.md"]`는 **chain directory**에서 resolve → cwd에 있는 파일을 못 찾음 → no-op

### 해결: `[Write to:]` 프리픽스 주입

```
Planner output: "plan.md"
  → pi-subagents가 [Write to: /path/to/chain-runs/{ID}/plan.md] 주입
  → Planner가 chain directory 경로 인식
  → task 파일도 같은 디렉토리에 작성

Worker reads: ["task1.md"]
  → pi-subagents가 [Read from: /path/to/chain-runs/{ID}/task1.md] 주입
  → chain directory에서 task 파일 자동 로드
```

### 실험 검증 (체인 28444dfa)

| 항목 | 결과 |
|------|------|
| Planner `[Write to:]` 수신 | ✅ `/tmp/.../28444dfa/plan.md` |
| Planner task 파일 위치 | ✅ chain directory에 task1.md, task2.md |
| Worker 1 `[Read from:]` 수신 | ✅ `/tmp/.../28444dfa/task1.md` |
| Worker 1 hello.ts 구현 | ✅ tsc 통과 |
| Worker 2 hello.test.ts | ✅ vitest 1/1 통과 |
| Worker 3 no-op (task3 없음) | ✅ 정상 |
| cwd 잔여 파일 | ✅ 없음 |

## 4. 성능 비교

### 4.1 입력 크기 (바이트)

| 메트릭 | pre-v3.5 (2) | v3.6.1 (17) | v3.6.2 (3) | v3.6.1→v3.6.2 |
|--------|:-----------:|:-----------:|:----------:|:-------------:|
| **P_in 평균** | 7,692 | 6,016 | 3,667 | **−39%** |
| **W_avg_in 평균** | 2,482 | 3,673 | 1,931 | **−47%** |
| **W_max_in 최대** | 3,083 | 11,491 | 4,117 | **−64%** |
| **Total_in 평균** | 10,174 | 18,792 | 11,838 | **−37%** |

### 4.2 입력 크기 감소 요인

**P_in −39%**: Planner 입력 감소는 과거 실행 대비 Task #0가 간결해진 것이 주요 요인. v3.6.2 샘플이 simple task 위주여서 과대 해석 주의.

**W_avg_in −47%**: Worker가 `[Read from:]` 프리픽스로 task 파일을 자동 수신하므로, Worker 템플릿에서 "Read taskN.md from the chain directory" 지시와 fallback 로직이 제거됨. Worker 입력이 task 내용 + RESULT 템플릿만으로 구성.

**W_max_in −64%**: v3.6.1에서 a15cee3f 체인의 W_max=11,491B이 이상치. v3.6.2에서는 W_max=4,117B로 상한이 낮아짐.

### 4.3 주의사항

- v3.6.2 샘플이 3개뿐이며, simple task 위주 (hello world, 소형 리팩토링)
- v3.6.1의 큰 Task #0 (10K+) 케이스와 직접 비교하면 v3.6.2의 수치가 과소평가될 수 있음
- W_avg_in 감소는 구조적 개선(`[Read from:]` auto-inject)의 효과이나, sample bias 가능성 존재

## 5. 안정성 개선

### 5.1 체인 실패 모드 비교

| 실패 모드 | v3.6.1 | v3.6.2 |
|-----------|--------|--------|
| Task 파일 경로 불일치 | ⚠️ Planner → cwd, Worker → chain dir | ✅ 둘 다 chain directory |
| 과거 실행 잔여 파일 간섭 | ⚠️ cwd에 task 파일 잔존 | ✅ chain directory에만 존재 |
| No-op 오진행 | ⚠️ 과거 task 파일 읽을 위험 | ✅ 파일 없으면 즉시 no-op |
| 0666bc7a 사고 재발 | ❌ Worker가 과거 task1.md 읽음 | ✅ 발생 불가 |

### 5.2 0666bc7a 사고 분석 (v3.6.1)

```
상황: reads:["task1.md"] + output:false
원인: Planner가 cwd에 task 파일 작성 → Worker가 chain directory에서 resolve → 파일 없음 → no-op
추가: 과거 체인의 cwd 잔여 task 파일을 읽을 위험도 존재
결과: 전체 체인 실패 (P_in=7,843B 낭비)
```

v3.6.2에서는 `output:"plan.md"` → `[Write to:]` 주입으로 Planner가 chain directory를 인식하여 이 사고가 불가능함.

## 6. 구조적 개선 내역

### v3.6 (Design Principles)

- **GGON 5원칙**: 최소 침투, 중앙 제어 존중, 인지 부하 관리, 관심사 격리, 리팩터 가치=다음 변경 비용 감소
- **리팩토링 설계 결정화**: 자동 금지 → 사용자 제안 + 승인 후 T₀ 포함
- **모순 6건 수정**: DP#4 읽기/수정 구분, History 정의 보완, Scout standalone 명시 등

### v3.6.1 (reads auto-inject)

- **Worker `reads:["taskN.md"]`**: task 파일 auto-inject로 Worker 입력 경량화
- **No-op Worker**: task 파일 없으면 즉시 no-op, read 재시도 금지
- **모순 8건 수정**: Past failures 복제, Rule 3/8/14, Worker SCOPE Tₖ 명확화 등

### v3.6.2 (Task 파일 경로 근원 해결)

- **Planner `output:"plan.md"`**: `[Write to:]` 프리픽스로 chain directory 경로 주입
- **Worker `reads:["taskN.md"]`**: `[Read from:]` 프리fl릭스로 task 파일 auto-inject
- **잔여 파일 위험 제거**: task 파일이 chain directory에만 존재
- **Worker template**: "Read taskN.md from the chain directory" → "Your task file taskN.md has been provided above"

## 7. 결론

v3.6.2는 task 파일 경로 문제를 근원적으로 해결함:

1. **안정성**: cwd 잔여 파일 간섭 위험 제거, 0666bc7a 사고 재발 불가
2. **효율**: Worker 입력 `−47%` (auto-inject로 중복 지시 제거)
3. **일관성**: `[Write to:]` / `[Read from:]` 프리픽스로 경로 관리를 pi-subagents에 위임

단, v3.6.2 샘플이 3개뿐이므로 대형 Task #0(10K+)에서의 성능은 추가 검증이 필요함. `plan.md`는 `[Write to:]` 주입을 위한 장치이며, 내용 자체는 부산물이다.