# Distributed Discrete Log Solver on PARCS

This repository demonstrates a **distributed approach** to solving the discrete logarithm problem (DLog) using [PARCS](https://github.com/lionell/parcs) on a **Docker Swarm** cluster. 

## Overview

- **Problem**: Given a prime \(p\), a generator \(g\) in \(\mathbb{Z}_p^*\), and a target \(h\), find \(x\) such that \(g^x \mod p = h\).
- **Approach**: We split the exponent search space \([0, p)\) across multiple **workers** (containers). Each worker checks a subset of exponents. As soon as one worker finds a valid \(x\), the computation stops.
- **PARCS**: A framework for orchestrating distributed computations on Docker Swarm. It automatically manages services, overlay networks, and environment variables to coordinate tasks.


