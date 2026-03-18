# Experiment Specification

## 1. Research question

Under a fixed compute budget, can an EP boundary layer reduce wasted search in Ramsey lower-bound construction without materially degrading the best legal witness found?

The first concrete instance is:

\[
R(3,13).
\]

## 2. Lower-bound task

Find a graph \(G\) on \(n\) vertices such that:

\[
\neg C_3(G)
\quad\text{and}\quad
\neg I_{13}(G).
\]

If such a graph exists, then:

\[
R(3,13)>n.
\]

## 3. Baseline

Plain search expands candidate graphs without EP pruning.

## 4. EP version

The EP version computes:

\[
E(G)=
w_1 R_{\mathrm{local}}(G)
+
w_2 R_{\mathrm{extend}}(G)
+
w_3 R_{\mathrm{pressure}}(G).
\]

Boundary decisions:

\[
E(G)>\Theta_{\mathrm{cut}}
\Rightarrow
\text{prune}
\]

\[
\Theta_{\mathrm{warn}}<E(G)\le \Theta_{\mathrm{cut}}
\Rightarrow
\text{restricted expansion}
\]

\[
E(G)\le \Theta_{\mathrm{warn}}
\Rightarrow
\text{full expansion}
\]

## 5. Search loop

For each candidate graph \(G\):

1. check legality
2. compute baseline quality
3. compute EP score
4. decide prune / restrict / expand
5. generate children by edge flips
6. keep highest-ranked surviving children

## 6. Key design principle

This system does **not** try to replace search.

It tries to decide which branches deserve search.

## 7. Expected outcomes

Success pattern:

\[
\mathrm{Saving}>0
\quad\text{and}\quad
\mathrm{Retention}\approx 1.
\]

Aggressive over-pruning pattern:

\[
\mathrm{Saving}>0
\quad\text{but}\quad
\mathrm{Retention}\ll 1.
\]

Weak-boundary pattern:

\[
\mathrm{Saving}\approx 0.
\]

## 8. Next implementation upgrades

1. Add CSV export
2. Add ablation runs
3. Add stronger legality proxies
4. Add algorithm-level rather than graph-level filtering
5. Add PDF-ready result tables
