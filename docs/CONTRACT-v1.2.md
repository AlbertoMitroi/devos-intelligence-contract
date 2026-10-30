# Contract v1.2

Accepted by the owner on 2026-10-30 (decisions C4 to C8 in [DECISIONS.md](DECISIONS.md)), tagged `v1.2.0`. Strictly additive to [v1.0](CONTRACT-v1.0.md) and [v1.1](CONTRACT-v1.1.md): every v1.0 and v1.1 generation validates against the v1.2 schemas, and a v1.1 consumer reads a v1.2 generation by the compatibility rules (unknown fields and kinds are kept, not interpreted). No new required capability. `schemaVersion` becomes `1.2` when a producer emits any item below.

| Area | Where | Decision |
|---|---|---|
| Observation `site` | `schema/v1/observation.schema.json` | C5 |
| Kinds from the Angular engine, link `renders`, `ui.route` with `path: null` | `schema/v1/kinds/` | C4 |
| In-process dispatch stated precisely (MediatR, NgRx) | `schema/v1/kinds/inprocess.*` | C8 |
| Constant call-site arguments used as destinations | `destinationParameter`, `schema/v1/kinds/call.argument.schema.json` | C7 (under C3, D20) |
| `index.sqlite` schema and `query` rows | `schema/index/v1/index.sql`, `schema/query/v1/` | C5 |
| System generation (federation), union copied | `schema/system/v1/` | C6 |

## Validating a record

A record is valid when it matches its file's schema in `schema/v1/` (as in v1.0) and, for an observation whose `kind` has a file in `schema/v1/kinds/`, that file too. The kind files use only the keywords every engine validator implements (`type`, `required`, `properties`, `additionalProperties`, `enum`, `const`, `pattern`, `items`, `minItems`, `minimum`), so engines apply them without a new validator. Observations of other kinds are checked by `observation.schema.json` alone.

## Observation `site`

- `site` (optional, an evidence id that is one of the record's `evidence`): the exact location of the fact, set by the adapter that made it. The call for calls, sends, publishes, invocations and call-site arguments; the mapping call or attribute for endpoints and hubs; the registration for DI; the name of the declaration for declaration-based facts (components, directives, handlers, actions, modules); the key for `config.key` and the rule for `http.proxy`.
- Other evidence of an observation may hold context (route groups, base-address configuration, the connection a call is made on).
- Producers of `1.2` set `site` on every observation they emit. Without `site` (v1.0 and v1.1), a consumer takes the first evidence ordered by (`path` ordinal, `startLine`, `startColumn`).

## Kinds from the Angular engine (C4)

Field shapes are the ones `angular-intelligence` 0.1.0 emits; `ext.angular` carries Angular detail. Every entity field holds a `ts:` id; `unresolved` where the table says so.

| Kind | Normalized fields |
|---|---|
| `ui.directive` | `directive` (entity), `selector` (string or null), `ext.angular.standalone` |
| `ui.pipe` | `pipe` (entity), `name` (pipe name or null), `ext.angular.standalone` |
| `ui.module` | `module` (entity), `declarations`, `imports`, `exports`, `bootstrap` (arrays of entities, sorted) |
| `ui.uses_directive` | `from` (component entity), `selector` (as written in the directive), `to` (directive entity or `unresolved` with `reason`) |
| `ui.route` | as v1.1, plus: `path` is the full path with one leading `/` when a root router configuration (`provideRouter`, `RouterModule.forRoot`) reaches the table; otherwise `path: null` with `ext.angular.relativePath` (the path as written) and `ext.angular.reason`. `component`, `loadComponent`, `loadChildren`: entity, `unresolved` or null; `redirectTo` (string or null); `guards` (guard kind to sorted entities); `resolvers` (key to entity); `ext.angular.lazy`, `outlet`, `pathMatch` |
| `http.interceptor` | `interceptor` (entity), `urlPrefix` (template the interceptor puts before the request URL, for example `{environment.gatewayUrl}`), `registered` (whether a provider registers it). An `http.call` whose base address comes from it has `baseAddress.source: interceptor` and `baseAddress.interceptor` |
| `http.proxy` | one record per rule of the development proxy (`proxy.conf.json` and literal `proxy.conf.js`): `prefix`, `target` (D20 destination, null when flagged secret), `secret`, `configuration`, `file`, `pathRewrite`, `nameSource: configuration`. An `http.call` routed through it has `baseAddress.source: proxy` |
| `realtime.connection` | client side of a hub connection: `route` (canonical route of the hub path, or null when no literal part is known), `urlTemplate`, `baseAddress` (same shape as `http.call`, or null), `client` (entity or null), `resolution` (`exact` when `route` is known, else `unresolved`) |
| `realtime.invoke` | client to server call on a connection: `route` and `hub` (the connection's route and URL template, `hub: unknown` when the connection is not known), `method`, `mode` (`invoke`, `send`, `stream`), `client`, `resolution`, `reason`. `realtime.subscribe` (v1.1) has the same fields without `mode` |
| `state.action` | `action` (entity of the action creator), `type` (the action type string or null), `mechanism` (`ngrx`) |
| `inprocess.send`, `inprocess.handler` | NgRx: see In-process dispatch |

| Link | Via | Rule |
|---|---|---|
| `renders` | `ui` | `ui.uses_component` to the `ui.component` of the used component, `exact`; `to: null`, `unresolved` with the observation's reason when the use is unresolved |

Real-time linking (federation): a `realtime.subscribe` or `realtime.invoke` belongs to the hub whose `realtime.hub.route` equals its `route`, after the connection's `baseAddress` routes it to an input. `pushes_to` goes from `realtime.send` of that hub to `realtime.subscribe` with the same method name compared ordinal and case-insensitive (the SignalR JavaScript client lowercases method names). v1.2 defines no link kind for `realtime.invoke`.

## In-process dispatch (C8)

The rules below make `Send(new Command(...))` to `IRequestHandler<Command>` an exact link.

`inprocess.send`:

- `request`: entity of the static type of the dispatched argument at the call. `Send(new SignContractCommand(...))` gives `T:...SignContractCommand`. A constructed generic type gives the entity of its definition, with `requestTypeArguments` (entities of the type arguments, in order).
- `sender`: the entity that contains the call (D6). `mechanism`: `mediatr`, `ngrx` or a convention name.
- `pattern`: `request` (MediatR `ISender.Send`, `IMediator.Send`), `notification` (`IPublisher.Publish`, `IMediator.Publish`; NgRx `Store.dispatch`), `stream` (`ISender.CreateStream`, `IMediator.CreateStream`). A record without `pattern` (v1.1): `request` for `mediatr`, `notification` for `ngrx`.
- `resolution`: `exact` when the static type is a concrete class, record or struct; `candidate` when it is an interface, an abstract class, a type parameter or `object` (the runtime type decides). Without `resolution`: `exact`.

`inprocess.handler`:

- One record per implemented handler interface; a class that handles three requests has three records.
- MediatR: `IRequestHandler<TRequest>` and `IRequestHandler<TRequest, TResponse>` give `pattern: request`, `INotificationHandler<TNotification>` gives `notification`, `IStreamRequestHandler<TRequest, TResponse>` gives `stream`. `request` is the entity of the type argument (definition plus `requestTypeArguments` when constructed).
- `handler`: the class that implements the interface (the type the container resolves), not the method. `handlerMethod` (optional): the method that implements `Handle` for this request.
- A handler whose type argument is a type parameter (open generic handler) has `resolution: candidate` and `request` set to the type parameter's first class or interface constraint; without a constraint it is not emitted and a diagnostic `unsupported` names it. Pipeline behaviors, pre-processors and post-processors are not handlers.
- NgRx: `handler` is the effect or the reducer, `ext.ngrx.role` (`effect` with `calls` and the reached `httpCalls`, or `reducer`).

`dispatches_to` (via `inprocess`), emitted by the engine inside a repository and by a federation across inputs (`scope: system`):

1. Handlers of a send: the same `mechanism`, the same `pattern` (after the defaults above) and the same `request`; when both sides carry `requestTypeArguments`, equal arguments.
2. `request` and `stream`: one handler gives one link with the send's resolution, so a concrete command with a single handler is `exact`. Several handlers give one link each, all `ambiguous` (the container picks one at run time). None gives one link with `to: null`, `unresolved`, and a reason naming the request.
3. `notification`: one link per handler, each with the send's resolution (fan-out, D18). None gives one `unresolved` link.
4. A send with `resolution: candidate`: one `candidate` link to each handler whose request type derives from or implements the static type; when the engine cannot list them, one `unresolved` link with a reason.
5. A generic request where only one side has `requestTypeArguments`: the link is `candidate` with a reason.
6. Evidence: the send's `site` and the handler's `site` (the whole evidence lists when `site` is absent).

## Constant call-site arguments used as destinations (C7, under D20)

When a destination (a SignalR method name, a topic or queue, a route) is a parameter of a helper and the value is a constant at the helper's call sites, often in another repository that consumes the helper as a package (`IMessageHubUtility.SendToAll("flowUpdated", ...)`), the value is recorded at the call site. This is an option of the producer; v1.2 defines the records, not when a producer turns it on.

1. **Template.** The observation inside the helper keeps its destination field null (or `unknown`, as its kind defines) with a resolution weaker than `exact`, and adds `destinationParameter`: `field` (the normalized field the parameter fills: `method` for `realtime.send`, `destination.name` for `messaging.*`, `route` or `urlTemplate` for `http.call`, `route` for `realtime.hub`), `parameter` (name as declared), `ordinal` (0-based position in the declaration; the `this` parameter of an extension method is 0).
2. **Call site.** One `call.argument` observation per call of a member whose parameter is a known destination parameter:
   - `caller` (the entity that contains the call), `callee` (the member as invoked: source symbol, interface member or `dotnet:pkg:` symbol), `parameter`, `ordinal`;
   - `value` and `valueSource`: `literal` (a string literal), `constant` (a constant field or local, or a concatenation of constants), `nameof`; anything else gives `value: null`, `valueSource: unknown`, `resolution: unresolved` and a `reason`;
   - `role`: `{ kind, field }` of the template (for example `{ "kind": "realtime.send", "field": "method" }`);
   - `basis`: `source` (the producer analysed the helper's body in the same run and saw the parameter reach the destination), `generation` (the helper's own generation, given to the producer as an input, has `destinationParameter` for that member), `configured` (the producer's configuration names member and parameter; its evidence has method `configured-convention`);
   - `resolution`: `exact` when `value` is known, else `unresolved`. `site`: the call.
3. **D20 limits.** Only parameters listed as destinations above produce `call.argument`; no other argument value is ever stored. A value or parameter the secret check flags is not stored: `value: null` with reason `secret`.
4. **Linking.** A linker (the engine inside a repository, a federation across inputs) that reaches a template observation through a call from caller C to callee M takes the `call.argument` of C, M (or the package or interface entity that maps to M through `implemented_by_package` and `implements`) and the template's `ordinal`, puts its value into `field`, and resolves the link with that value. Call sites with different values give separate links. Without a matching `call.argument`, linking stays as in v1.1 (`candidate` or `unresolved`, with the reason that no call-site value is recorded).

## Index and query (C5)

`index.sqlite` is derived from the NDJSON graph, which stays the source of truth. It lets one reader (the MCP server) query generations of every producer with the same SQL.

### Tables

[`schema/index/v1/index.sql`](../schema/index/v1/index.sql) is normative (index schema `1`):

- **base**: created by every producer exactly as written (names, columns, column order, indexes, FTS5 table `search`);
- **evidence**: optional (`relation_evidence`, `observation_evidence`, `link_evidence`, `evidence_snippet` and their indexes); a consumer uses them when present;
- **system**: written by a federation only (`inputs`, `packages`, `traces`).

No other table or index. Columns:

| Table | Content |
|---|---|
| `meta` | `schemaVersion`, `commit`, `engine` (`name@version`) always; `indexSchema` (`1`), `status` (manifest status), `coverage` (canonical JSON of the manifest's `coverage.summary`) from 1.2. A system generation adds `generationType: system`, `system`, `systemFormat`, `configurationHash`, and `commit` is its `system:{sha256}` |
| `entities`, `projects` | the record's fields shown, `json` the canonical record; `projects.path` is the project path, or `project` for an analysis context |
| `declarations` | `path`, `line`, `col` of the `span` start |
| `evidence` | span, `method`, `context`, `text` (the redacted snippet of the start line, or null) |
| `relations` | `path`, `line`: the first evidence by (`path` ordinal, `startLine`, `startColumn`); all evidence in `relation_evidence` |
| `observations` | `path`, `line`: the `site` evidence, else the first evidence by (`path`, `startLine`, `startColumn`); `json` the canonical record |
| `links` | `from_obs`, `to_obs`: the sides' `observation` (for `implemented_by_package`, the sides' entity) |
| `search` | `kind: entity` (text `{name} {signature} {kind}`), `kind: snippet` (the redacted line), optional `kind: observation` (the kind and its normalized string fields) |

Canonical dump (`query <generation> dump`): every table except `search_*` and `sqlite_*`, ordered by name; each row the canonical JSON array of its column values; rows sorted ordinally; one `table<TAB>row` line each. Two runs on the same input give identical dumps.

### `query` verbs

Exit codes: `0` results, `2` usage error or no `index.sqlite`, `3` ambiguous name (JSON: the candidate rows, none picked), `4` no results (JSON `[]`). `--json` prints canonical JSON; text output is producer-specific. A name resolves as an exact id, else a unique `name` (.NET also accepts `Type.Member` and prefers a type over its constructors). In a partial generation the no-results text says that an absence of results is not proof of absence.

| Verb | JSON (schema in `schema/query/v1/`) |
|---|---|
| `symbol <name or id>` | one object `{entity, declarations: [{path, line}]}` (`symbol`) |
| `refs <symbol> [--usage u]` | `{from_id, usage, path, line, text}`: one row per relation, or per usage evidence when `relation_evidence` exists (`refs`) |
| `callers`, `callees <symbol> [--depth N]` | `{depth, of, other, path, line}`; optional `kind`, `resolution`, `declared_target` (`callers`) |
| `impl <symbol>` | `{kind, from_id, path, line}` (`impl`) |
| `di <service>` | `{kind, path, line, json}`, `json` the observation as text (`di`) |
| `routes [--route prefix]` (alias `endpoints`) | the `ui.route` or `http.endpoint` record plus `at` (`path:line`) (`routes`) |
| `http [--route prefix]` | the `http.call` record plus `at`; optional `targets: [{link, kind, resolution, reason, to}]` (`http`) |
| `search <text> [--kind k] [--limit n]` | `{ref, kind, text}`, optional `at`; terms quoted and joined with AND, ranked by bm25 then `ref` (`search`) |
| `calls-to`, `messages`, `trace` | optional verbs (`calls-to`, `messages`, `trace`) |
| `dump` | text only |
| exit code 3 | `[{id, kind, name, signature}]` (`ambiguous`) |

## System generation (C6)

A federation combines included input generations into one generation. Every rule is additive: a consumer that ignores the new files and fields reads it as a v1 generation whose ids carry a prefix. The union of the inputs is copied (decision C6), so a system generation is self-contained and its index can be rebuilt from its files.

### Layout

The v1.0 layout, plus:

| Path | Content |
|---|---|
| `manifest.json` | v1 fields plus `generationType: system`, `systemFormat` (`1.0`), `system` (name), `inputs` (`name`, `commit`, `manifestSha256`, `included`). `commit` is `system:{sha256}` over the inputs' (name, commit, manifest sha256); `repository.remoteUrl` is null; `analysisContexts` and `coverage.projects` are the inputs' own, prefixed; `coverage.inputs` counts included and excluded inputs |
| `inputs.ndjson` | one `recordType: input` record per input: `id` (input name), repository, commit, dirty, engine, image digest, schema version, status, `manifestSha256`, `included`, `verification` (`result`: `ok`, `ok-with-defects`, `failed`; `errors`, `references`, `notes`) |
| `graph/*.ndjson`, `snippets.ndjson` | the union of the included inputs' records, prefixed, plus system links and system diagnostics |
| `graph/packages.ndjson` | `recordType: packageResolution` (`pkr:` ids): one per consumer input, package and consumed version |
| `graph/traces.ndjson` | `recordType: trace` (`trc:` ids): end-to-end paths across two or more system links |
| `index.sqlite` | the index above over the union, plus the system tables |
| `context/` | `overview.md`, `service-map.md`, `repositories/{input}.md`, `contracts/{name}.md`, `traces.md` |

Generated sources (`generated/`) of the inputs are not copied: evidence with `store: generation` points into the input generation named by its `input` field. Schemas: [`schema/system/v1/`](../schema/system/v1/).

### Identity

- Input name: `^[a-z0-9][a-z0-9-]*$`, unique in the system.
- A copied record: `id` becomes `{input}/{id}`; every string inside it that is a record id (`ev:`, `obs:`, `ctx:`, `prj:`, `snip:`, `rel:`, `decl:`, `lnk:`, `diag:` followed by 32 hex) or an entity id (`dotnet:`, `ts:`) gets the same prefix (`leasing/dotnet:src/...`); free-text fields (`text`, `message`, `reason`, `signature`, `name`, `fullName`, `urlTemplate`, `routeTemplate`, `path`, `file`, `key`, `value`, `template`, `documentationId`) are never rewritten. The record gains `input`. Paths stay repository-relative.
- Validation: the `schema/v1` schemas (and `schema/v1/kinds`) apply with every pattern that starts with `^` widened to `^(?:[a-z0-9][a-z0-9-]*/)?...`.
- System records keep unprefixed ids over their canonical identifying fields: links `lnk:`, diagnostics `diag:`, package resolutions `pkr:`, traces `trc:`.

### System links

A `graph/links.ndjson` record with `scope: system` (v1 link schema plus `system-link.schema.json`). Kinds: `configured_route` (HTTP), `consumes_contract` (messaging), `pushes_to` (real time), `implemented_by_package`, `possible_communication`, `dispatches_to`.

| Field | Meaning |
|---|---|
| `from`, `to` | `input`, `observation` (prefixed id or null), `kind`, `project` (path inside that input, or null), `entity` (prefixed id or null). `to` is null when `resolution` is `unresolved` |
| `from.through` | the observation sits in a package's source and the behaviour belongs to a consumer: `package` (id, version, produced version), `packageEntity`, `sourceEntity`, `packageLink`, `observationInput`, `observationProject`, `versionMatch`; then `from.input` and `from.entity` are the consumer's call site |
| `from.alsoObservations`, `to.alsoObservations` | further observations of the same logical endpoint |
| `match` | what matched: HTTP `method`, `route`, `endpointRoute`, `baseAddress`, `targets`; messaging `contractIdentity`, `contract`, `destination`, `transports`; real time `method`, `sendMethod`, `hub` |
| `resolution`, `reason` | the weakest part; a non-exact link names the parts that are not exact |
| `versionMatch`, `package` | `implemented_by_package` only (`exact`, `different`, `unknown`) |
| `evidence` | prefixed evidence ids of both sides, at least one |

### Package resolution and trace records

- Package resolution: `ecosystem` (`nuget`, `npm`), `packageId`, `version` (consumed), `consumer` (`input`, `projects`), `producer` (`input`, `project`, `method`: `packageId`, `assemblyName` or `npmName`; `packageId`, `packageVersion`, `repository`, `commit`, `tag` always null because generations record no tags; a package no input produces has no record), `resolution`, `versionMatch`, `reason`, `entities` (`used`, `resolved`, `missing`).
- Trace: `start`, `end` (entity or observation ids), `inputs`, `links` (system link ids, at least two), `segments` in order (`type: link` with the link and its sides, or `type: inside` with `kind` `call`, `implementation`, `runtime-target`, `dispatch` or `member`, the entity reached, `resolution`, `evidence`), `resolution` (weakest), `weakest` (`segment` index and resolution).

## What each producer changes to emit 1.2

| Producer | Changes |
|---|---|
| `angular-intelligence` | `schemaVersion: 1.2`; vendor `schema/` at `v1.2.0` and validate observations with `schema/v1/kinds`; set `site`; emit `pattern: notification` on NgRx sends and handlers; add `meta.indexSchema`, `status`, `coverage`; `relations.path/line` from the first evidence by location; optionally the evidence tables and `search` kind `observation`. Its kinds need no other change |
| `dotnet-intelligence` | `schemaVersion: 1.2`; vendor and validate as above; set `site` (replaces the index heuristic); in-process dispatch as written (`handlerMethod`, `requestTypeArguments`, open generic handlers, candidate sends); optionally `destinationParameter` and `call.argument` (C7) |
| `intelligence-federation` | vendor `schema/system/v1` instead of `schema/system-proposal/`; `systemFormat: 1.0`, `schemaVersion: 1.2`; `meta.commit` in the index; link real time through `realtime.connection` and method names case-insensitive; substitute `call.argument` values (C7); `dispatches_to` rules above |
| `intelligence-mcp` | read the index by `schema/index/v1/index.sql`; prefer `site` for locations |
