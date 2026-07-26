# Proof Notes: Almost Symmetric Games

These notes track the exact theorem statements, proof dependencies, and remaining audit risks for the manuscript **Almost Symmetric Games: Incentive-Preserving Projections and Certified Equilibrium Computation**.

## 1. Formal objects

A finite game is

\[
\Gamma=(N,(A_i)_{i\in N},(u_i)_{i\in N}).
\]

A relabeling `g` contains a player permutation `pi_g` and action bijections

\[
\tau_{g,i}:A_i\to A_{\pi_g(i)}.
\]

It maps profiles by

\[
(ga)_{\pi_g(i)}=\tau_{g,i}(a_i),
\]

and games by

\[
(g\Gamma)_{\pi_g(i)}(ga)=u_i(a).
\]

For a finite group `G`,

\[
\operatorname{Fix}(G)=\{\widehat\Gamma:g\widehat\Gamma=\widehat\Gamma\ \forall g\in G\}.
\]

A mixed profile respects `G` when its probabilities are constant under the induced action on the disjoint union of player-action pairs.

## 2. Strategic distance

For compatible games `Gamma` and `Gamma'`, define the residual

\[
r_i(a)=u_i(a)-v_i(a)
\]

and the maximum pairwise difference

\[
d_{\rm dev}(\Gamma,\Gamma')
=
\max_{i,a_{-i},a_i,b_i}
|r_i(a_i,a_{-i})-r_i(b_i,a_{-i})|.
\]

Equivalently,

\[
d_{\rm dev}(\Gamma,\Gamma')
=
\max_{i,a_{-i}}
\left(\max_{a_i}r_i(a_i,a_{-i})-
\min_{a_i}r_i(a_i,a_{-i})\right).
\]

### Proposition: quotient norm

`d_dev` is a seminorm on payoff tensors. Its kernel is exactly the nonstrategic subspace

\[
n_i(a_i,a_{-i})=c_i(a_{-i}).
\]

Hence it is a norm after quotienting by nonstrategic components.

Proof: it is the maximum of absolute linear functionals. Distance zero means each residual slice is constant over the player's own action.

### Raw payoff comparison

\[
d_{\rm dev}(\Gamma,\Gamma')
\le 2\|\Gamma-\Gamma'\|_\infty.
\]

There is no universal reverse inequality because arbitrarily large nonstrategic components have zero strategic distance.

## 3. Strategic symmetry defect

Define

\[
\delta_G(\Gamma)
=
\min_{\widehat\Gamma\in\operatorname{Fix}(G)}
 d_{\rm dev}(\Gamma,\widehat\Gamma).
\]

For a closed linear class `C`, such as zero-sum or common-payoff games, define the structured version

\[
\delta_{G,C}(\Gamma)
=
\min_{\widehat\Gamma\in\operatorname{Fix}(G)\cap C}
 d_{\rm dev}(\Gamma,\widehat\Gamma).
\]

Important: the unrestricted and structured defects need not coincide. Every zero-sum theorem in the paper uses the zero-sum structured defect.

## 4. Projection LP

For every surrogate payoff coordinate introduce `uhat_i(a)`. For every slice `(i,a_-i)`, introduce lower and upper residual variables `L` and `U`, plus objective `t`:

\[
\begin{array}{ll}
\min&t\\
\text{s.t.}&L_{i,a_{-i}}\le u_i(a)-\widehat u_i(a)\le U_{i,a_{-i}},\\
&U_{i,a_{-i}}-L_{i,a_{-i}}\le t,\\
&\widehat u_i(a)=\widehat u_{\pi_g(i)}(ga)\quad\forall g\in S.
\end{array}
\]

Here `S` is a generating set. For fixed surrogate payoffs, the minimum feasible width of each residual interval equals the range of that slice; therefore the optimum is exactly `delta_G`.

If

\[
P=n\prod_i|A_i|,
\qquad
Q=\sum_i\prod_{j\ne i}|A_j|,
\]

the compact LP uses `P + 2Q + 1` variables and `2P + Q` strategic inequalities, plus sparse generator and structure equalities.

## 5. Maximum-mean-cycle characterization

This is the main structural strengthening beyond the initial roadmap.

### Orbit graph

Vertices are payoff-coordinate orbits `[i,a]` under `G`. For each ordered unilateral comparison from baseline action `b_i` to action `a_i` against the same `a_-i`, add an edge

\[
[i,(b_i,a_{-i})]\to[i,(a_i,a_{-i})]
\]

with label

\[
c_e=u_i(a_i,a_{-i})-u_i(b_i,a_{-i}).
\]

An invariant surrogate is one potential `x_v` per orbit. Its error on edge `e` is

\[
|x_{\rm head(e)}-x_{\rm tail(e)}-c_e|.
\]

Because every ordered comparison has its reverse, error at most `t` is equivalent to the one-sided difference constraints

\[
x_{\rm head(e)}-x_{\rm tail(e)}\le c_e+t.
\]

A system of difference constraints is feasible iff every directed cycle has nonnegative total edge length. Thus

\[
\boxed{
\delta_G(\Gamma)
=
\max_C
\left(-\frac1{|C|}\sum_{e\in C}c_e\right).
}
\]

At the critical shift there is no negative cycle. Shortest-path potentials provide a nearest invariant surrogate. Applying Karp's algorithm to weights `-c_e` computes the value and a critical cycle in polynomial time.

### Points that need careful wording

- Self-loops must be retained; a self-loop can itself certify inconsistency after orbit identification.
- Parallel edges are allowed. For the one-sided system, only the minimum label for a fixed ordered endpoint pair matters.
- The reverse comparison is what supplies the lower half of the absolute-error constraint.
- The cycle theorem applies to the unrestricted projection. Adding zero-sum or team equalities may destroy the pure difference-constraint form, so structured projections continue to use the LP.

### Numerical audit

`tests/test_cycle.py` compares the cycle method with the LP on 100 randomized games. The largest observed disagreement is below `5e-9`.

## 6. Mixed incentive transfer

If

\[
d_{\rm dev}(\Gamma,\widehat\Gamma)\le\delta,
\]

then for every player, opponent mixture, and two own mixed strategies, the difference between their two deviation incentives across the games is at most `delta`.

Reason: at every pure opponent profile, all residual values lie in an interval of width `delta`; two convex combinations differ by at most the interval width. Average over opponent profiles.

Therefore, if `sigma` is an `epsilon`-Nash equilibrium of the surrogate,

\[
\operatorname{Reg}_i^\Gamma(\sigma)
\le \epsilon+\delta.
\]

## 7. Existence of an invariant approximate equilibrium

Every exactly invariant finite game has an invariant Nash equilibrium. A self-contained proof:

1. The fixed-profile set `X^G` is nonempty, compact, and convex.
2. The logit-response map is equivariant in an invariant game, so it maps `X^G` into itself.
3. Brouwer gives an invariant logit fixed point at every precision.
4. Along a convergent sequence as precision tends to infinity, strictly suboptimal actions receive vanishing mass.
5. The limit is an invariant Nash equilibrium.

Combining this with a nearest invariant surrogate and transfer yields a `G`-respecting `delta_G`-Nash equilibrium in every finite game.

## 8. Tightness

Player 1 has `k` actions, one with payoff 1 and the others with payoff 0, independent of player 2. The group cycles all `k` actions.

- Every invariant surrogate equalizes those action payoffs, so `delta_G = 1`.
- The only invariant strategy is uniform.
- Its regret is `1 - 1/k`.

Thus the coefficient one in the transfer/existence theorem is asymptotically optimal.

## 9. Reynolds averaging

Define

\[
\mathcal P_G\Gamma=|G|^{-1}\sum_{g\in G}g\Gamma,
\qquad
\eta_G=\max_g d_{\rm dev}(\Gamma,g\Gamma).
\]

Then

\[
\delta_G
\le d_{\rm dev}(\Gamma,\mathcal P_G\Gamma)
\le \eta_G
\le 2\delta_G.
\]

Proof ingredients:

- the average is invariant;
- convexity of the seminorm;
- for any invariant surrogate `H`,
  \[
  d(\Gamma,g\Gamma)\le d(\Gamma,H)+d(gH,g\Gamma)=2d(\Gamma,H).
  \]

The average is computed from payoff-coordinate orbits, not by enumerating the group.

## 10. Zero-sum results

For a matrix game,

\[
\operatorname{Gap}_A(x,y)
=
\max_i(Ay)_i-\min_j(x^T A)_j
\]

is the sum of the two player regrets.

Using the zero-sum structured defect:

- each player regret of a projected equilibrium is at most `delta_G^zs`;
- total saddle gap is at most `2 delta_G^zs`.

The direct invariant-gap LP minimizes

\[
\alpha-\beta
\]

subject to

\[
Ay\le\alpha\mathbf 1,
\qquad
x^TA\ge\beta\mathbf 1^T,
\]

simplex constraints, and orbit-equality constraints. For fixed `(x,y)`, the best `alpha` and `beta` make the objective exactly the saddle gap.

For an exactly invariant matrix and invariant opponent strategy, best-response values are constant on action orbits; one best-response constraint per orbit suffices.

## 11. Statistical stability

Distance to a fixed closed set is one-Lipschitz:

\[
|\delta_{G,C}(\Gamma)-\delta_{G,C}(\widetilde\Gamma)|
\le d_{\rm dev}(\Gamma,\widetilde\Gamma).
\]

If each estimated payoff entry is within `xi` of the truth, then

\[
d_{\rm dev}(\Gamma,\widetilde\Gamma)\le2\xi.
\]

For `P` bounded means, each estimated from `M` independent samples, Hoeffding plus a union bound gives

\[
\xi_M=\sqrt{\frac{\log(2P/\alpha)}{2M}}.
\]

An exact equilibrium of the projected estimate has true per-player regret at most

\[
\widehat\delta+2\xi_M,
\]

and zero-sum saddle gap at most

\[
2\widehat\delta+4\xi_M.
\]

## 12. Claims intentionally not made

- A small strategic defect does **not** imply a welfare guarantee.
- The paper does not solve approximate symmetry discovery; `G` is supplied.
- Polynomial time is with respect to the explicit normal-form table.
- General-sum Nash computation does not become tractable merely because projection is tractable.
- The maximum-mean-cycle solver is for the unrestricted projection; structured classes use the LP.

## 13. Highest-priority proof audit

Before submission, an independent reader should check:

1. the orientation/sign convention in the cycle formula;
2. self-loops and parallel-edge compression in the cycle graph;
3. the exact relationship between global action orbits and strategy-equality constraints when a symmetry swaps players;
4. that every zero-sum claim consistently uses the structured defect;
5. AAAI page-limit placement of proof sketches versus supplement.
