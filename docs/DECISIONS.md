# Decisions

## C1: One home for the contract

- **Context:** three engines produce or combine generations; the contract lived in `dotnet-intelligence`.
- **Choice:** this repository owns `schema/` and the contract documents; engines vendor a tagged copy with a drift check.
- **Status:** accepted (owner: all projects under `devos/`).

## C2: v1.1 is additive

- **Choice:** everything in `CONTRACT-v1.1.md` is optional for v1.0 consumers; no required capability is added.
- **Status:** draft until the first engine emits it and its fixtures pass.

## C3 (D20): destinations from configuration

- **Context:** topics, queues and base addresses usually live in configuration; without them messages and HTTP calls cannot be linked across repositories.
- **Choice:** store a configuration value only when an adapter uses it as a destination (topic, queue, exchange, base address, hub route) and neither key nor value is flagged secret; it goes into that observation's `destination` or `baseAddress` with `nameSource: configuration`. Every other configuration value stays out.
- **Reason:** without destinations, messages and HTTP calls cannot be linked across repositories.
- **Revisit:** if a destination value is found to carry a secret that the secret flag missed: tighten the flag, never drop the check.
- **Status:** accepted by the owner on 2026-10-29 (deviation from rule 1.4.6 of the dotnet prompt, recorded in every engine's DECISIONS.md when implemented).
