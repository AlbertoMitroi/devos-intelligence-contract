# Contract tests

`python3 -m unittest discover -s tests -v` from the repository root (needs `pip install -r tests/requirements.txt`).

| File | Source |
|---|---|
| `examples/angular-fixtures.ndjson` | Records of the v1.2 kinds as `angular-intelligence` 0.1.0 (commit `7ef64c5`) emits them for its fixtures a02, a05, a06, a07, a10 and a11, copied unchanged |
| `examples/v1.2-constructed.ndjson` | Written by hand for what no engine emits yet (`site`, `destinationParameter`, `call.argument`, `pattern`, `handlerMethod`, `ui.pipe`); ids are synthetic |
| `examples/v1.2-invalid.ndjson` | One defect per line; each must fail |
| `query-examples/angular/` | `query --json` output of `angular-intelligence` 0.1.0 on the `lab-web-angular` generation; the file name starts with the row schema name |

Real generations: every folder with a `manifest.json` in `DEVOS_GENERATIONS` (default: `_generations` next to the checkout), and system generations listed in `DEVOS_SYSTEM_GENERATIONS`.
