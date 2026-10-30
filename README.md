# intelligence-contract

The shared contract of the intelligence engines: the format of a **generation** (one repository at one commit) and of a **system generation** (several generations linked across repositories).

- Producers: `dotnet-intelligence`, `angular-intelligence`; combiner: `intelligence-federation`.
- Schemas: [`schema/v1/`](schema/v1/) (v1.0 and the additive v1.1 changes; every v1.0 generation validates). Rules: [`docs/CONTRACT-v1.0.md`](docs/CONTRACT-v1.0.md) (published), [`docs/CONTRACT-v1.1.md`](docs/CONTRACT-v1.1.md) (draft, additive).
- Engines vendor a copy of `schema/` at a tagged version and fail their build when the copy drifts.

Source of v1.0: `dotnet-intelligence` commit `d1248f3623fb03cfb10bcbec491b4b2098f9913e` (`schema/v1`, `docs/CONTRACT.md`), moved here unchanged.

## License

MIT, see [LICENSE](LICENSE).
