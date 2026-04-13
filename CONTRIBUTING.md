# Contributing to FluBroad

Thanks for your interest. FluBroad is a young framework — your contribution will be visible and consequential.

---

## Ways to contribute

### Build a Skill package

The highest-value contribution. Pick a biomedical domain (oncology, immunology, neuroscience, rare disease) and wrap it as a Skill.

Start here: **[docs/skill-spec.md](docs/skill-spec.md)** — full spec, package layout, agent authoring rules, testing requirements, and publishing instructions.

The virology reference implementation is [biovoice-agents](https://github.com/yiweixidu/biovoice-agents). Read `biovoice/skill.py` to see what a complete manifest looks like.

### Add a framework agent

Common agents (PubMed, Europe PMC, Semantic Scholar, PDB, UniProt) live in the framework. If you have a new public database that is broadly useful across domains, add it here.

Agent rules: `fetch()` must be async, never raise from `fetch()`, every item dict needs `source / title / abstract / pmid / year / citation_count / fulltext_available`. See `docs/skill-spec.md §4`.

### Fix a bug or improve the core

Open an issue first for anything beyond a trivial fix. Describe the problem, not the solution. We will align on approach before you write code.

---

## Process

1. Fork, create a branch: `git checkout -b feat/your-thing`
2. Write tests. New agents need at least mock-HTTP unit tests. New manifest fields need a manifest validation test.
3. `pytest tests/ -m "not integration and not eval"` must pass clean.
4. Open a PR with a one-paragraph description of what it does and why it belongs in the framework (vs. a Skill package).

---

## Skill registry

Once your Skill is published on PyPI, open a PR to add it to the registry table in `README.md`:

```markdown
| `your-domain` | `flubroad-skill-your-domain` | Short description | @yourhandle | alpha |
```

Status options: `alpha` / `beta` / `stable`.

---

## License

Framework contributions are MIT. Skill packages choose their own license (CC BY-NC 4.0 is recommended for academic Skills, MIT for fully open ones).

---

Questions? Open an issue at [github.com/yiweixidu/flubroad](https://github.com/yiweixidu/flubroad).
