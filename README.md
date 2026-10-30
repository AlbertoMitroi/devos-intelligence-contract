# intelligence-contract

The shared contract of the intelligence engines: the format of a **generation** (one repository at one commit) and of a **system generation** (several generations linked across repositories).

- Producers: `dotnet-intelligence`, `angular-intelligence`; combiner: `intelligence-federation`.
- Rules: [`docs/CONTRACT-v1.0.md`](docs/CONTRACT-v1.0.md), [`docs/CONTRACT-v1.1.md`](docs/CONTRACT-v1.1.md), [`docs/CONTRACT-v1.2.md`](docs/CONTRACT-v1.2.md); each minor only adds. Decisions: [`docs/DECISIONS.md`](docs/DECISIONS.md).
- Schemas:

| Path | Content |
|---|---|
| [`schema/v1/`](schema/v1/) | Records of a generation (every minor; each change only widens what validates) |
| [`schema/v1/kinds/`](schema/v1/kinds/) | Normalized fields per observation kind (v1.2) |
| [`schema/system/v1/`](schema/system/v1/) | System generation records (v1.2) |
| [`schema/index/v1/index.sql`](schema/index/v1/index.sql) | `index.sqlite` tables (v1.2) |
| [`schema/query/v1/`](schema/query/v1/) | `query --json` rows (v1.2) |

- Engines vendor a copy of `schema/` at a tag (`v1.2.0`) and fail their build when the copy drifts.
- Tests: `python3 -m unittest discover -s tests -v` (needs `pip install -r tests/requirements.txt`). They check that the v1 schemas only widen since v1.1, that the examples in `tests/examples/` pass (and the invalid ones fail), and, when present, that every generation in `../_generations` (or `DEVOS_GENERATIONS`) and every system generation in `DEVOS_SYSTEM_GENERATIONS` validates and its `index.sqlite` matches `index.sql`.

Source of v1.0: `dotnet-intelligence` commit `d1248f3623fb03cfb10bcbec491b4b2098f9913e` (`schema/v1`, `docs/CONTRACT.md`), moved here unchanged.

## License

MIT, see [LICENSE](LICENSE).
