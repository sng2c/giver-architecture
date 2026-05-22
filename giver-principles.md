# Giver 원칙 v3.5.4

## 제1원리: 컨텍스트는 스티어링과 코딩 I/O로 분해된다

에이전트가 코딩을 하면 코딩 I/O가 발생한다. 소스 파일, 테스트 출력, 에러 로그, 디버그 트레이스. 이 코딩 I/O는 컨텍스트를 오염시킨다.

$$
\text{context}(A) = \underbrace{\text{steer}(A)}_{\text{결정, 방향 지시}} \cup \underbrace{\text{io}(A)}_{\text{소스, 테스트, 로그}} \quad \text{where } \text{steer}(A) \cap \text{io}(A) = \emptyset
$$

스티어링이 코딩 I/O에 묻히면 에이전트가 방향을 잃는다. 이것이 모든 원리의 출발점이다.

## 제2원리: 격리는 스티어링만 하류로 전달한다

에이전트 경계에서 코딩 I/O를 버리고 스티어링만 전달하면, 하류 에이전트는 오염되지 않은 방향 지시를 받는다.

$$
G \xrightarrow{T_0 \in \mathcal{S}} P \xrightarrow{T_k \in \mathcal{S}} W_k \xrightarrow{R_k \in \mathcal{S}} G
$$

각 화살표에서 $\text{io}(\cdot)$는 버려지고 $\text{steer}(\cdot)$만 전달된다. 이것이 "격리"다.

$$
\text{isolate}(A \to B) = \text{steer}(A) \quad \text{(코딩 I/O는 전달 안 됨)}
$$

### 격리의 결과: 컨텍스트가 일정하게 유지된다

격리가 없으면 코딩 I/O가 복리로 누적된다:

$$
|\text{context}_{\text{mono}}(n)| = |\text{context}_{\text{mono}}(1)| \cdot r^{n-1} \quad \text{where } r > 1
$$

격리가 있으면 각 에이전트는 자기 입력 크기에 비례하는 컨텍스트만 처리한다:

$$
|\text{context}(W_k)| \approx O(|T_k|) \quad \text{(누적 없음, 일정)}
$$

| 경계 | 전달 전 (오염) | 전달 후 (격리) | 격리율 |
|------|---------------|---------------|--------|
| $G \to P$ | $|\text{context}(G)|$ | $|T_0|$ | $\approx 99\%$ |
| $P \to W_k$ | $|T_0|$ | $|T_k|$ | $83\text{--}93\%$ |
| $W \to G$ | $|\text{io}(W)|$ | $|R_k|$ | $\approx 98\%$ |

## 제3원리: Giver는 코딩 I/O에 노출되지 않는다

Worker가 864KB의 코드를 작성해도, Giver가 받는 건 RESULT뿐이다. 코딩 I/O가 Giver로 역류하지 않는다.

$$
\text{io}(W_k) \notin \text{context}(G) \quad \text{(Worker의 코딩 I/O가 Giver에 역류 안 됨)}
$$

Giver는 커지지 않는다. 이것이 파이프라인이 Monolithic보다 강건한 이유다.

## 제4원리: 서브에이전트는 부모 컨텍스트와 독립이다

모든 서브에이전트는 fresh로 실행된다. 부모의 대화, 이전 체인의 결과, 다른 에이전트의 I/O — 모두 격리된다.

$$
\text{context}(A) \cap \text{context}(G) = \emptyset \quad \text{for } A \in \{P, S, W_1, \ldots, W_n\}
$$

이 독립성이 3-tier의 기반이다. Giver가 500KB의 대화를 가져도, Planner는 5.6KB의 $T_0$만 받는다.

## 제5원리: 파이프라인은 조합에 의한 히스토리다

{previous}는 이전 단계의 출력만 직접 전달하지만, 그 출력은 이미 그 이전 단계의 출력을 포함하여 만들어진 것이다. 따라서 정보는 조합에 의해 누적되어 하류로 흐른다.

$$
R_1 = W_2(T_2, R_0) \quad \Rightarrow \quad R_1 \text{는 } R_0\text{를 내포한다}
$$

$$
R_2 = W_3(T_3, R_1) \quad \Rightarrow \quad R_2 \text{는 } R_0, R_1\text{을 내포한다}
$$

이것이 히스토리다. 하지만 이 히스토리는 $R_k \in \mathcal{S}$에 의해 손실 압축된다. 각 단계에서 코딩 I/O는 버려지고 스티어링만 남으므로, 누적은 $O(|T_k|)$에 바운드된다.

$$
|R_k| \leq |\text{steer}(W_k)| + |\text{curate}(R_{k-1})| \quad \text{(히스토리는 압축되어 전달)}
$$

직접 누적 $\bigcup_{i=0}^{k-1} R_i$와 조합 누적 $R_k = W_k(\ldots, R_{k-1})$의 차이는 정보 손실에 있다. 조합 누적은 각 단계에서 $\text{io}(\cdot)$를 버리므로, 체인이 길어져도 $|R_k|$는 일정 범위에 머문다.

## 제6원리: RESULT는 코딩 I/O를 포함하지 않는다

Worker의 결과에 코드 본문이 포함되면, 그것이 하류로 전달될 때 코딩 I/O의 역류가 된다. 따라서 RESULT는 스티어링만 포함한다.

$$
R_k = (\text{Files}_k, \text{Signatures}_k, \text{Summary}_k) \quad \text{where } \text{code} \notin R_k
$$

코드 본문이 필요한 Worker는 SCOPE 내에서 파일을 직접 읽는다. RESULT를 통한 I/O 역류를 원천 차단한다.

## 집합과 기호

$$
\begin{aligned}
\mathcal{C} &= \text{컨텍스트 집합 (대화, 코드, 입출력)} \\
\mathcal{S} &= \text{스티어링 집합 (결정, 방향 지시)} \\
\mathcal{I} &= \text{코딩 I/O 집합 (소스, 테스트 출력, 에러 로그)} \\
\mathcal{F} &= \text{파일 경로 집합} \\
\mathcal{D} &= \{(\sigma, f) \mid \sigma = \text{시그니처}, f \in \mathcal{F}\} \quad \text{의존성 튜플}
\end{aligned}
$$

$$
\mathcal{S} \cap \mathcal{I} = \emptyset \quad \text{(스티어링과 코딩 I/O는 서로소)}
$$

## 데이터 구조

$$
T_0 = \text{Goal} \times \text{Background} \times \text{PastFailures} \times \text{Constraints} \times \text{ImportsNeeded}
$$

$$
T_k = \text{curate}_k(T_0) \times \text{TargetFiles}_k \times \text{ImportsNeeded}_k \times \text{FileRel}_k \quad (T_k \in \mathcal{S})
$$

$$
R_k = \text{Files}_k \times \text{Signatures}_k \times \text{Summary}_k \quad (R_k \in \mathcal{S}, \text{code} \notin R_k)
$$

Planner는 $T_0$를 Worker별로 큐레이팅하여 독립 태스크를 생성한다:

$$
P: T_0 \to \{T_1, T_2, \ldots, T_n\} \quad \text{where } T_j \cap T_k \approx \emptyset \quad (j \neq k)
$$

## 함수

$$
\begin{aligned}
G &: \mathcal{C} \to T_0 && G(\mathcal{C}) \in \mathcal{S} \quad \text{대화에서 결정만 추출} \\
P &: T_0 \to \{T_k\} && P(T_0) \subseteq \mathcal{S} \quad \text{큐레이팅만, 파일 읽기 없음} \\
S &: \mathcal{D}_{\text{dirs}} \to \mathcal{D}_{\text{recon}} && \text{디렉토리 → 시그니처 + 구조} \\
W &: T_k \times R_{k-1} \to R_k && W_k\text{의 치역 } R_k \in \mathcal{S} \quad \text{코드 본문 제외}
\end{aligned}
$$

## 파이프라인

$$
G \xrightarrow{\text{Recon}} S \xrightarrow{\text{recon}} G \xrightarrow{T_0} P \xrightarrow{\{T_k\}} \prod_{k=1}^{n} W_k
$$

$$
\begin{aligned}
W_1 &: (T_1) \to R_0 \\
W_2 &: (T_2, R_0) \to R_1 \\
&\vdots \\
W_n &: (T_n, R_{n-2}) \to R_{n-1}
\end{aligned}
$$

각 경계에서 전달되는 것과 버려지는 것:

$$
G \xrightarrow{\text{steer}} P: \quad T_0 \in \mathcal{S}, \quad \text{io}(G) \text{ 버림}
$$

$$
P \xrightarrow{\text{steer}} W_k: \quad T_k \in \mathcal{S}, \quad \text{io}(P) \text{ 버림}, \quad T_j (j \neq k) \text{ 버림}
$$

$$
W_k \xrightarrow{\text{steer}} G: \quad R_k \in \mathcal{S}, \quad \text{io}(W_k) \text{ 버림}
$$

코딩 I/O는 각 경계에서 버려진다. 이것이 스티어링 격리의 실체다.