# Decisions

## C1: One home for the contract

- **Context:** three engines produce or combine generations; the contract lived in `dotnet-intelligence`.
- **Choice:** this repository owns `schema/` and the contract documents; engines vendor a tagged copy with a drift check.
- **Status:** accepted (owner: all projects under `devos/`).

## C2: v1.1 is additive

- **Choice:** everything in `CONTRACT-v1.1.md` is optional for v1.0 consumers; no required capability is added.
- **Status:** published with `v1.2.0` (both engines emit 1.1; their generations validate, `tests/test_contract.py`).

## C3 (D20): destinations from configuration

- **Context:** topics, queues and base addresses usually live in configuration; without them messages and HTTP calls cannot be linked across repositories.
- **Choice:** store a configuration value only when an adapter uses it as a destination (topic, queue, exchange, base address, hub route) and neither key nor value is flagged secret; it goes into that observation's `destination` or `baseAddress` with `nameSource: configuration`. Every other configuration value stays out.
- **Reason:** without destinations, messages and HTTP calls cannot be linked across repositories.
- **Revisit:** if a destination value is found to carry a secret that the secret flag missed: tighten the flag, never drop the check.
- **Status:** accepted by the owner on 2026-10-29 (deviation from rule 1.4.6 of the dotnet prompt, recorded in every engine's DECISIONS.md when implemented).

## C4: Angular kinds in the contract

- **Context:** `angular-intelligence` emits kinds that v1.1 does not name (its A9) and routes no root router reaches (its A12); without `realtime.connection` a federation cannot link SignalR between front end and back end.
- **Choice:** v1.2 adds `ui.directive`, `ui.pipe`, `ui.module`, `ui.uses_directive`, `http.interceptor`, `http.proxy`, `realtime.connection`, `realtime.invoke`, `state.action`, the link `renders`, and `ui.route` with `path: null` plus `ext.angular.relativePath` and a reason, with the field shapes the engine emits today (`schema/v1/kinds/`).
- **Status:** accepted by the owner on 2026-10-30.

## C5: One index and query shape, observation `site`

- **Context:** one MCP server reads `index.sqlite` of every producer; the engines located observations differently.
- **Choice:** `schema/index/v1/index.sql` is normative (base tables as the Angular engine writes them, optional evidence tables from the .NET engine, system tables from federation; meta `indexSchema`, `status`, `coverage`); `query --json` rows have one shape per verb (`schema/query/v1/`); observations get an optional `site` evidence id set by the adapter, which replaces location heuristics.
- **Status:** accepted by the owner on 2026-10-30.

## C6: System generation with the union copied

- **Context:** federation combines generations; a consumer should open one folder.
- **Choice:** the format of `intelligence-federation` `docs/SYSTEM-GENERATION.md` (commit `bb3a2ea`) becomes `schema/system/v1/` and the system section of `CONTRACT-v1.2.md`; the inputs' records are copied with prefixed ids, not referenced by digest.
- **Reason:** a self-contained generation whose index can be rebuilt from its files; size is small once compressed in the registry.
- **Revisit:** if system generations outgrow the registry or the reader's memory.
- **Status:** accepted by the owner on 2026-10-30.

## C7: Constant call-site arguments used as destinations

- **Context:** a destination passed as an argument to a package helper (`IMessageHubUtility.SendToAll("flowUpdated", ...)`) is known only at the call site, often in another repository; without it the lab's SignalR links stay `candidate`.
- **Choice:** the helper's observation names the parameter (`destinationParameter`); call sites record the constant value in `call.argument` observations; linkers substitute it. Same limit as C3 (D20): only destination parameters, never other values, never secrets. Optional for producers.
- **Status:** accepted by the owner on 2026-10-30.

## C8: In-process dispatch stated precisely

- **Context:** the owner asked that the .NET engine emit exact mediator links (`Send(new Command)` to `IRequestHandler<Command>`).
- **Choice:** `CONTRACT-v1.2.md` fixes the request identity (static type of the argument, generic definition plus type arguments), the handler records (one per implemented interface, the class as `handler`), `pattern` defaults and the `dispatches_to` resolution rules.
- **Status:** accepted by the owner on 2026-10-30.
