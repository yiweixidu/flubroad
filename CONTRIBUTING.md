# Contributing to BioAgent

Thanks for your interest. BioAgent is a young platform — your contribution will directly shape how biomedical labs interact with AI.

---

## Ways to contribute

### Build a Tier package

The highest-value contribution. Pick a tier — Precision (molecular tasks), Fusion (multi-omics data), Strategy (grants), or Horizontal (compliance/audit) — and package it as an installable Tier.

Start here: **[docs/tier-spec.md](docs/tier-spec.md)** — full spec, package layout, container authoring rules, ETL adapter rules, testing requirements, and publishing instructions.

Reference implementations:
- **Precision containers**: [`bioagent-tier2-precision`](https://github.com/your-org/bioagent-tier2-precision) — DNABERT‑2, SEHI‑PPI, ESM‑2 containers.
- **Compliance templates**: [`bioagent-l0-loi25`](https://github.com/your-org/bioagent-l0-loi25) — Loi 25 self‑assessment report generator.

### Add a model container

If you have a new molecular model (e.g., for RNA structure, TCR‑epitope binding, enzyme kinetics), wrap it as a container and register it in the L2.5 Model Zoo.

Rules for containers:
- Must inherit from `bioagent.model_zoo.base.BaseModelContainer`.
- `predict()` must be `async`, never raise; return errors as structured dicts with `"result"` and `"provenance"`.
- Provide `health()` and `metadata()` implementing the fields specified in `docs/tier-spec.md §4`.

### Add an ETL adapter

For Tier 3 Fusion, build an adapter that ingests raw lab data (e.g., mass‑spec `.raw`, flow cytometry `.fcs`, plate reader `.txt`) and outputs standardized `Study` and `Assay` objects.

Adapters must inherit from `bioagent.data.BaseLoader` and implement `load()`, `transform()`, `store()`. See `docs/tier-spec.md §5`.

### Add a compliance or grant template

For L0 or Tier 4, create templates that generate Loi 25 / GDPR reports or funder‑specific grant documents (CIHR, NSERC, NIH). These are plain functions or classes that accept audit trail / project data and return Markdown or DOCX.

### Fix a bug or improve the core

Open an issue first for anything beyond a trivial fix. Describe the problem, not the solution. We will align on approach before you write code.

---

## Process

1. Fork, create a branch: `git checkout -b feat/your-thing`
2. Write tests. New containers need at least a mock‑inference unit test. New manifest fields need a manifest validation test.
3. `pytest tests/ -m "not integration and not slow"` must pass clean.
4. Open a PR with a one‑paragraph description of what it does and which tier/architecture gap it addresses (e.g., *“Resolves Gap 2: adds an antibody‑antigen binding container”*).

---

## Tier registry

Once your Tier package is published on PyPI, open a PR to add it to the registry table in `README.md`:

```markdown
| Tier 2 – antibody‑design | `bioagent-tier2-antibody-design` | ProtGPT2 + IgFold container | @yourhandle | alpha |
```

Status options: `alpha` / `beta` / `stable`.

---

## License

Core framework contributions are MIT.

Tier packages choose their own license. **CC BY‑NC 4.0** is recommended for academic/non‑profit tiers; **MIT** for fully open ones.

---

Questions? Open an issue at [github.com/your-org/bioagent](https://github.com/your-org/bioagent).