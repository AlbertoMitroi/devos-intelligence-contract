# Contract v1.1

Published with `v1.2.0`; [v1.2](CONTRACT-v1.2.md) adds to it. Strictly additive to [v1.0](CONTRACT-v1.0.md): a v1.0 consumer reads a v1.1 generation by the compatibility rules (unknown fields and kinds are kept, not interpreted). No new required capability. `schemaVersion` becomes `1.1` when an engine emits any of the items below.

## Identity

- TypeScript entities: `ts:{projectPath}:{modulePath}#{symbolPath}`. `projectPath` is the repository-relative directory of the Angular project (from `angular.json`, `project.json` or `package.json`); `modulePath` is the repository-relative file without extension; `symbolPath` is the dotted path of the declaration inside the module (`OrdersService.load`, `default` for default exports). Overloads add `({parameter types as written})`.
- npm package symbols: `ts:pkg:{packageName}@{version}:{modulePath}#{symbolPath}`.
- All other v1.0 identity rules apply unchanged.

## Project record

| Field | Meaning |
|---|---|
| `language` | `csharp` or `typescript` |
| `packageId`, `packageVersion`, `isPackable` | .NET: evaluated `PackageId`, `Version`, `IsPackable`; lets a federation resolve `dotnet:pkg:{packageId}@{version}` to this project's source |
| `npmName`, `npmVersion` | TypeScript: `name` and `version` of the project's `package.json`, when it is a library |

## Messaging

`messaging.publish` and `messaging.subscribe` gain normalized `transport` (`rabbitmq`, `azure-service-bus`, `kafka`, `in-memory`, `unknown`) and `destination` (`{ kind: exchange | queue | topic | subscription, name, nameSource: literal | configuration | convention }`). Environment-specific transports are listed, not chosen: `transports: [...]` when configuration selects one per environment.

## New observation kinds

| Kind | Normalized fields |
|---|---|
| `inprocess.send` | `request` (entity), `sender`, `mechanism` (`mediatr` or convention name) |
| `inprocess.handler` | `request` (entity), `handler` (entity), `mechanism` |
| `eventstore.append` | `event` (entity), `stream` (template or `unknown`), `store` (`marten`, convention) |
| `eventstore.projection` | `projection` (entity), `events` (entities), `lifecycle` (`inline`, `async`, `live`) |
| `realtime.hub` | `hub` (entity), `route` |
| `realtime.send` | `hub` (entity or `unknown`), `method` (client method name), `audience` (`all`, `users`, `group`, `unknown`) |
| `realtime.subscribe` | client side: `route` or hub name, `method` |
| `search.index` | `index` (name or template), `document` (entity) |
| `workflow.process` | `processId`, `name`, `file`, `lanes` |
| `workflow.node` | `processId`, `nodeId`, `nodeType` (`userTask`, `serviceTask`, `startEvent`, `endEvent`, `intermediateEvent`, `boundaryEvent`, `gateway`, `subProcess`, `callActivity`), `name`, `lane` |
| `workflow.flow` | `processId`, `from`, `to` (node ids), `condition` (text, redacted) |
| `workflow.handler` | `processId` (or `*`), `nodeName` or `eventName`, `handler` (entity), `role` (convention role, for example `serviceTask`), `resolution` |
| `data.table` | `entity` (mapped type), `table`, `schema`, `store` (`efcore`, `marten-document`) |
| `infra.resource` | `provider`, `type`, `name` (Terraform and similar; values are never stored) |
| `ui.component` | `component` (entity), `selector`, `template` (path) |
| `ui.uses_component` | `from` (component entity), `selector`, `to` (component entity or `unresolved`) |
| `ui.route` | `path` (full, with parents), `component` or `loadChildren` / `loadComponent` target, `guards` |

## New link kinds (federation and engines)

| Kind | Meaning |
|---|---|
| `dispatches_to` | in-process dispatch: `inprocess.send` → `inprocess.handler`, `workflow.node` → `workflow.handler` |
| `implemented_by_package` | federation only: a `dotnet:pkg:` or `ts:pkg:` entity to the source entity in the repository that produces the package; carries `versionMatch` (`exact`, `different`, `unknown`) |
| `pushes_to` | `realtime.send` → `realtime.subscribe` |

## Configuration values used as destinations (decision D20, accepted)

v1.0 never stores configuration values. v1.1 proposes one exception: a value that an adapter uses as a destination (topic, queue, exchange, base address, hub route) is stored in that observation's `destination` or `baseAddress`, with `nameSource: configuration`, and only when the key and the value are not flagged secret. Every other value stays out. Status: **accepted by the owner on 2026-10-29**.

## Schema changes (`schema/v1/`, all optional)

The v1 schema files describe both minors; every change only widens what validates, so every v1.0 generation still validates.

| File | Change |
|---|---|
| `entity.schema.json` | `id` pattern `^(dotnet|ts):` |
| `relation.schema.json` | `usage` adds `decorator`, `import` |
| `link.schema.json` | `via` adds `inprocess` (`dispatches_to` from `inprocess.send`), `workflow` (`workflow.node` to `workflow.handler`), `realtime` (`pushes_to`), `ui` (TypeScript UI links), `package` (`implemented_by_package`) |
| `project.schema.json` | optional `language`, `packageId`, `packageVersion`, `isPackable`, `npmName`, `npmVersion` |
| `manifest.schema.json` | `roslyn` and `sdks` are no longer required (.NET engines keep emitting them); optional `toolchain` (`name`, `version`) for engines without Roslyn |
| `analysis-context.schema.json` | `targetFramework` and `preprocessorSymbols` are no longer required (.NET engines keep emitting them) |

## System generation (federation)

Superseded by the system section of [v1.2](CONTRACT-v1.2.md). A system generation has the v1.0 layout plus `inputs.ndjson` (one record per input generation: repository, commit, engine, image digest, manifest sha256, schema version) and cross-repository records whose ids are prefixed by the input they come from (`{inputId}/{recordId}`) so records never collide. Links across inputs use the kinds above and v1.0's `consumes_contract`, `configured_route`, `possible_communication`.
