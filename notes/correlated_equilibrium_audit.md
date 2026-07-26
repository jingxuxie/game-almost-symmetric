# Correlated-Equilibrium Extension: Novelty and Claim Audit

This note records the closest correlated-equilibrium literature and the exact
boundary of the new general-sum extension.

## Classical correlated equilibrium

Aumann (1974) introduced correlated equilibrium. Hart and Schmeidler (1989)
gave an existence proof via linear duality, and Papadimitriou and Roughgarden
(2008) studied efficient computation in succinct multi-player games.

The manuscript does **not** claim that correlated equilibrium, its linear
program, or the averaging of feasible points in a convex polytope is new.

## Symmetric correlated solutions

Amir, Belkov, and Evstigneev (2017) classify symmetric correlated equilibria in
symmetric two-player, two-action games. Stein, Ozdaglar, and Parrilo (2013)
study exchangeable equilibrium, a conditionally i.i.d. refinement lying between
symmetric Nash and symmetric correlated equilibrium. Tewolde et al. (2025)
observe that a symmetry-respecting correlation device can coordinate among
high-payoff relabeled profiles, but intentionally focus their complexity theory
on Nash equilibrium.

The present contribution differs in four ways:

1. the symmetry group may arbitrarily relabel players and actions in any finite
   normal-form game;
2. the game need only be approximately symmetric in unilateral incentives;
3. CE and CCE violations transfer from a symmetric surrogate with an explicit
   additive `delta_G` certificate; and
4. the implementation solves a welfare-optimal invariant CE with one variable
   per pure-profile orbit and evaluates the certificate in the original game.

The role-assignment theorem is not a claim that correlation can improve welfare
in general. It gives a sharp, transparent separation between two operational
interpretations of symmetry:

- invariant independent randomization has welfare `n! / n^n`;
- an invariant correlation device has welfare one.

## Equivariant learned solvers

Marris et al. (2022) learn permutation-equivariant neural solvers for Nash,
correlated, and coarse-correlated equilibrium. Liu et al. (2024) develop
NfgTransformer for permutation-equivariant normal-form-game representation and
equilibrium-related tasks.

Those methods learn across a distribution of games. This project instead takes
one explicit game and one supplied relabeling group, computes the minimum
strategic projection error, and returns a checkable equilibrium certificate.
The manuscript must not claim the first symmetry-aware CE solver or the first
use of equivariance in CE computation.

## Defensible new claims

The expanded draft can claim:

1. `epsilon + delta` transfer for CE and CCE under MPD strategic distance;
2. existence of a `G`-respecting `delta_G`-CE and `delta_G`-CCE in every finite
   game through projection and group averaging;
3. preservation of every invariant linear selection objective when averaging
   CE/CCE in an exact `G`-invariant game;
4. an explicit profile-orbit LP for invariant CE/CCE under arbitrary supplied
   player/action relabelings;
5. an end-to-end polynomial-time general-sum projection--CE--certificate
   pipeline for explicit games; and
6. the invariant-independent versus invariant-correlated role-assignment
   separation.

## Claims intentionally excluded

The draft does not claim:

- a new definition or existence theorem for CE itself;
- a faster worst-case algorithm for unrestricted CE;
- that CE is always an appropriate behavioral model;
- that correlation is available in decentralized systems without a shared
  signal, mediator, or common random seed;
- welfare transfer from strategic distance alone; or
- tractability in compact graphical or sequential representations.
