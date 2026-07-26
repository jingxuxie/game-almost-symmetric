# Proof Notes: Almost Symmetric Games

These notes state the manuscript's theorem stack, proof dependencies, and claim
boundaries in a form suitable for line-by-line auditing.

## 1. Relabelings and fixed subspaces

A finite normal-form game is

\[
\Gamma=(N,(A_i)_{i\in N},(u_i)_{i\in N}).
\]

A relabeling `g` consists of a player permutation `pi_g` and action bijections

\[
\tau_{g,i}:A_i\to A_{\pi_g(i)}.
\]

It maps profiles and games by

\[
(ga)_{\pi_g(i)}=\tau_{g,i}(a_i),
\qquad
(g\Gamma)_{\pi_g(i)}(ga)=u_i(a).
\]

For a finite group `G`,

\[
\operatorname{Fix}(G)
=
\{\widehat\Gamma:g\widehat\Gamma=\widehat\Gamma\ \forall g\in G\}.
\]

A mixed profile respects `G` when probabilities are invariant under the induced
action on the disjoint union of player-action coordinates.

## 2. Strategic distance

For compatible games `Gamma` and `H`, let

\[
r_i(a)=u_i(a)-h_i(a).
\]

Define maximum pairwise difference

\[
d_{\rm dev}(\Gamma,H)
=
\max_{i,a_{-i},a_i,b_i}
|r_i(a_i,a_{-i})-r_i(b_i,a_{-i})|.
\]

Equivalently,

\[
d_{\rm dev}(\Gamma,H)
=
\max_{i,a_{-i}}
\left(\max_{a_i}r_i(a_i,a_{-i})-
\min_{a_i}r_i(a_i,a_{-i})\right).
\]

### Quotient-norm proposition

`d_dev` is a relabeling-invariant seminorm. Its kernel is exactly the
nonstrategic subspace

\[
n_i(a_i,a_{-i})=c_i(a_{-i}).
\]

Thus it is a norm after quotienting games by opponent-action-dependent payoff
components. It also satisfies

\[
d_{\rm dev}(\Gamma,H)
\le 2\|\Gamma-H\|_\infty,
\]

with no reverse inequality up to a universal constant.

## 3. Strategic symmetry defect

Define

\[
\delta_G(\Gamma)
=
\min_{\widehat\Gamma\in\operatorname{Fix}(G)}
 d_{\rm dev}(\Gamma,\widehat\Gamma).
\]

For a closed linear class `C`, such as zero-sum or common-payoff games, define

\[
\delta_{G,C}(\Gamma)
=
\min_{\widehat\Gamma\in\operatorname{Fix}(G)\cap C}
 d_{\rm dev}(\Gamma,\widehat\Gamma).
\]

The unrestricted and structured defects can differ. Every zero-sum theorem in
the paper uses the zero-sum structured defect.

## 4. Projection LP

For every surrogate payoff coordinate introduce `uhat_i(a)`. For every slice
`(i,a_-i)`, introduce lower and upper residual bounds `L` and `U`, plus
objective `t`:

\[
\begin{array}{ll}
\min&t\\
\text{s.t.}&L_{i,a_{-i}}\le u_i(a)-\widehat u_i(a)
\le U_{i,a_{-i}},\\
&U_{i,a_{-i}}-L_{i,a_{-i}}\le t,\\
&\widehat u_i(a)=\widehat u_{\pi_g(i)}(ga)
\quad\forall g\in S.
\end{array}
\]

Here `S` is a generating set. For a fixed surrogate, the smallest interval
width in a residual slice is exactly that slice's MPD contribution. Generator
invariance is equivalent to group invariance. Hence the optimum is exactly
`delta_G`.

If

\[
P=n\prod_i|A_i|,
\qquad
Q=\sum_i\prod_{j\ne i}|A_j|,
\]

the compact LP uses `P + 2Q + 1` variables and `2P + Q` strategic
inequalities, plus sparse generator and optional structure equalities.

## 5. Maximum-mean-cycle characterization

### Orbit graph

Vertices are payoff-coordinate orbits `[i,a]`. For every ordered unilateral
comparison from action `b_i` to `a_i` against `a_-i`, add an edge

\[
[i,(b_i,a_{-i})]\to[i,(a_i,a_{-i})]
\]

with label

\[
c_e=u_i(a_i,a_{-i})-u_i(b_i,a_{-i}).
\]

An invariant surrogate assigns one potential `x_v` per vertex. Error at most
`t` means

\[
|x_{\rm head(e)}-x_{\rm tail(e)}-c_e|\le t.
\]

Because the reverse ordered comparison is also present, this is equivalent to

\[
x_{\rm head(e)}-x_{\rm tail(e)}\le c_e+t
\quad\forall e.
\]

A difference-constraint system is feasible exactly when every directed cycle
has nonnegative total length. Therefore

\[
\boxed{
\delta_G(\Gamma)
=
\max_C
\left(-\frac1{|C|}\sum_{e\in C}c_e\right).
}
\]

Self-loops are included. Parallel upper-bound edges with the same endpoints can
be replaced by the smallest label.

### Constructive upper bound

At the critical shift, all edge lengths `c_e + delta_G` have no negative cycle.
Shortest-path potentials give a feasible invariant surrogate at distance
`delta_G`.

### Certified lower-bound witness

Let `w_e=-c_e` and `lambda=delta_G`. The reduced graph with weights
`w_e-lambda` has no positive cycle and at least one zero-weight critical cycle.
Max-plus path potentials make every reduced edge inequality have nonnegative
slack. Around a zero-weight cycle the slacks telescope and sum to zero, so every
critical-cycle edge is tight. Searching the tight-edge graph yields a closed
cycle whose mean is exactly `lambda`.

This avoids the unjustified shortcut of treating a Karp dynamic-programming
predecessor chain as automatically critical.

### Scope

The cycle theorem applies to the unrestricted projection. Adding zero-sum or
team equalities can destroy the pure difference-constraint form; structured
projections use the LP.

## 6. Mixed incentive transfer

If

\[
d_{\rm dev}(\Gamma,\widehat\Gamma)\le\delta,
\]

then for every player, opponent mixture, and two own mixed strategies, the
corresponding incentive difference changes by at most `delta`. In every pure
opponent slice, residuals lie in an interval of width `delta`; two convex
combinations remain within that interval, and averaging over opponent profiles
preserves the bound.

Therefore an `epsilon`-Nash equilibrium of the surrogate satisfies

\[
\operatorname{Reg}_i^\Gamma(\sigma)
\le \epsilon+\delta.
\]

## 7. Existence of an invariant approximate equilibrium

Every exactly invariant finite game has an invariant Nash equilibrium:

1. the fixed-profile set is nonempty, compact, and convex;
2. the logit-response map is equivariant and preserves the fixed set;
3. Brouwer gives an invariant logit fixed point at every precision;
4. any limit as precision diverges assigns positive mass only to best responses.

Combining this fact with a nearest invariant surrogate and equilibrium transfer
yields a `G`-respecting `delta_G`-Nash equilibrium in every finite game.

## 8. Tightness of the transfer coefficient

Player 1 has `k` cyclically identified actions, one with payoff one and the rest
with payoff zero. Player 2 is strategically irrelevant.

- Every invariant surrogate equalizes the action payoffs, so `delta_G=1`.
- The only invariant strategy of player 1 is uniform.
- Its regret is `1-1/k`.

Thus the coefficient one is asymptotically optimal.

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

The first inequality is feasibility, the second is convexity, and the third is
the triangle inequality through an optimal invariant surrogate.

### Tightness

For the two-block size-`d` construction in the supplement,

\[
\delta_{G_d}=1,
\qquad
 d_{\rm dev}(\Gamma_d,\mathcal P_{G_d}\Gamma_d)
=2-\frac{2}{d^2}.
\]

A two-edge critical cycle gives the lower bound one; the zero surrogate gives
the matching upper bound. Direct orbit averaging gives the stated residual
range. Hence the factor two is asymptotically tight.

## 10. Nested groups

For

\[
G_0\subseteq G_1\subseteq\cdots\subseteq G_K,
\]

the fixed subspaces shrink, so

\[
\delta_{G_0}\le\delta_{G_1}\le\cdots\le\delta_{G_K}.
\]

Meanwhile the number of action and payoff-coordinate orbits cannot increase.
This is the certified compression--fidelity frontier.

## 11. Zero-sum results

For a matrix game,

\[
\operatorname{Gap}_A(x,y)
=
\max_i(Ay)_i-\min_j(x^TA)_j
\]

is the sum of the two player regrets.

Using the zero-sum structured defect:

- each transferred player regret is at most `delta_G^zs`;
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

simplex constraints, and global action-orbit equalities. For an exactly
invariant matrix, best-response values are constant on the relevant action
orbits, so one representative constraint per orbit is sufficient.

## 12. Statistical stability

Distance to a fixed closed set is one-Lipschitz:

\[
|\delta_{G,C}(\Gamma)-\delta_{G,C}(\widetilde\Gamma)|
\le d_{\rm dev}(\Gamma,\widetilde\Gamma).
\]

If every payoff estimate has entrywise error at most `xi`, then

\[
d_{\rm dev}(\Gamma,\widetilde\Gamma)\le2\xi.
\]

For `P` bounded means with `M` independent samples each, Hoeffding and a union
bound give

\[
\xi_M=\sqrt{\frac{\log(2P/\alpha)}{2M}}.
\]

An exact equilibrium of the projected estimate has true per-player regret at
most

\[
\widehat\delta+2\xi_M,
\]

and zero-sum saddle gap at most

\[
2\widehat\delta+4\xi_M.
\]

## 13. Numerical audit

The independent checks now cover:

- LP versus cycle defect on randomized games;
- witness closure and critical mean;
- self-loop and parallel-edge obstructions;
- reconstructed-surrogate distance;
- player-swapping action orbits;
- transfer and zero-sum certificates;
- both sharpness families;
- finite-sample coverage;
- full versus orbit-reduced solver equivalence.

## 14. Claims intentionally not made

- Approximate symmetry in games or MARL is not claimed to be new as a broad
  topic.
- MPD itself is not introduced by this paper.
- The candidate group is supplied rather than discovered.
- General-sum Nash computation does not become tractable merely because
  projection is tractable.
- Small strategic defect does not imply welfare preservation.
- Polynomial time is with respect to the explicit normal-form table.
- Stochastic, extensive-form, graphical, and polymatrix extensions remain
  future work.
