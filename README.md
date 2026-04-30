```markdown
# BioAgent — On-Premises Multimodal Molecular Intelligence Research Partner

> DNA/protein language models, literature knowledge engines, and wet-lab feedback loops packaged as pluggable feature packs. Deploy on your lab’s own GPU. Not a cloud API wrapper — an AI wet-lab team member.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)

BioAgent is an **open-source, non-profit framework** that equips biomedical laboratories with four independently deployable AI tiers — Foundation, Precision, Fusion, and Strategy — wrapped by cross-cutting zero-trust audit and active learning loops. It transforms a single-GPU server into a long-term AI research partner that can interpret sequences, predict molecular interactions, generate testable hypotheses, and co-author grant proposals — all while keeping sensitive data strictly on‑premises.

```
pip install bioagent
pip install bioagent-tier2-precision    # DNA + protein model containers
```

---

## The problem this solves

- **Generic AI doesn’t understand your project** – off‑the‑shelf LLMs lack depth in influenza cross‑species transmission, rare variant effects, or antibody engineering, and they cannot learn from unpublished data.
- **Data can never leave the lab** – under Quebec’s Law 25 (Loi 25) and CIHR data policies, clinical samples and unpublished sequences must not touch any third‑party cloud.
- **Fragmented toolchain** – researchers jump between a dozen separate tools for sequence interpretation, interaction prediction, knowledge graphs, and grant writing, with no unified, traceable workflow.
- **Grant applications lack a technical moat** – labs need a partner that can co‑produce patentable outputs and co‑author major funding proposals, not another software subscription.

BioAgent’s four tiers and seven‑layer architecture solve each of these gaps.

| Layer | What it contains | Who builds it |
|-------|------------------|---------------|
| **Framework** (`bioagent`) | Tier orchestration, MLOps fine‑tuning pipeline, inference API gateway, zero‑trust audit plane, RAG engine | BioAgent core team |
| **Tier packages** (`bioagent-tier2-*` etc.) | Dedicated model containers (DNABERT‑2, SEHI‑PPI, ESM‑2), ETL adapters, domain manifests | Domain experts + core team |

A bioinformatician writes a short `TierManifest`; the framework handles the rest.

---

## Quickstart

### Run a sequence variant interpretation (Tier 2 Precision)

```bash
pip install bioagent bioagent-tier2-precision

cp .env.example .env    # configure LOCAL_MODEL_DIR or Ollama endpoint

bioagent run \
  --tier precision \
  --model dna-language-model \
  "chr11:534289 A>G effect on FOXA1 binding site"
```

Output in `./output/`:
- `variant_interpretation.md` – structured explanation with evidence and literature references
- `ppi_prediction.json` – if an interacting host factor is identified
- `audit_trail.json` – complete, tamper‑evident data lineage

### Fully local (zero external API calls)

```bash
bioagent run --tier foundation,precision --llm ollama/biot5+-7b "your query"
```

### Docker (recommended for labs)

```bash
docker compose up    # Gradio UI at :7860, ChromaDB at :8001, local LLM at :11434
```

---

## Architecture

```
User query
    │
    ├── Tier selection & L2 Core Orchestrator
    │
    ├── [L4 Knowledge Layer]  ← Skill manifests, multi‑source ETL pipelines
    │
    ├── [L2.5 Model Zoo]      ← DNA language model, PPI predictor, protein folding container
    │
    ├── [L3 Persistence]      ← SQLite, ChromaDB, Neo4j, model version registry, time‑series experiment DB
    │
    ├── [L0 Compliance]       ← zero‑trust audit, data lineage, RBAC, hardware isolation proof
    │
    ├── Active Learning Loop (L2 horizontal)
    │     └── Hypothesis engine → experiment feedback → MLOps fine‑tuning trigger
    │
    └── Output pipeline
          ├── Interpretation report (python-docx)
          ├── Grant proposal draft (custom RAG)
          ├── Knowledge graph visualization (Cytoscape.js)
          └── Compliance self‑report (Loi 25)
```

```
bioagent/
├── tier1/               # Foundation: base models, domain corpus, MLOps fine‑tuning pipeline
├── tier2/               # Precision: model containers (DNA, PPI, protein), A/B testing framework
│   ├── dna_lm/
│   ├── ppi_predictor/
│   └── protein_lm/
├── tier3/               # Fusion: multi‑source ETL, graph DB (Neo4j), cross‑project data governance
├── tier4/               # Strategy: grant RAG pipeline, milestone tracker, budget generator
├── horizontal/          # Audit plane, hypothesis engine, experimental feedback loop manager
├── model_zoo/           # Container registry, versioning, canary deployment
├── api/                 # FastAPI inference gateway
├── ui/                  # Gradio panels (hypothesis dashboard, project dashboard, graph viewer)
└── core/                # Orchestrator, task state machine, tier loader
```

---

## The Tier interface

A tier package (e.g., Tier 2 Precision) is a Python package that:
1. Provides one or more `BaseModelContainer` subclasses
2. Declares a `TierManifest` listing models, endpoints, and hardware requirements
3. Registers everything via `pyproject.toml` entry points

```python
# tier2_precision/manifest.py
from bioagent.core.tier import TierManifest

manifest = TierManifest(
    name="precision",
    version="1.0.0",
    display_name="Tier 2: Precision Molecular Intelligence",
    models={
        "dna-language-model": "tier2_precision.containers.dna_lm:DNALanguageModelContainer",
        "ppi-predictor": "tier2_precision.containers.ppi:PPIPredictorContainer",
        "protein-lm": "tier2_precision.containers.protein:ProteinLMContainer",
    },
    inference_gateway=True,
    requires_gpu=True,
    min_vram_gb=24,
)
```

```toml
# pyproject.toml
[project.entry-points."bioagent.tiers"]
precision = "tier2_precision.manifest:manifest"
```

Full specification: [docs/tier-spec.md](docs/tier-spec.md)

---

## Building a new Tier component

```bash
bioagent new-container antibody-design --tier precision
```

Scaffolds:

```
bioagent-tier2-antibody-design/
├── antibody_design/
│   ├── container.py         # inherits BaseModelContainer
│   ├── model/               # model weights or download script
│   └── manifest.py
├── tests/
└── pyproject.toml
```

Then plug it into the Model Zoo:

```bash
pip install -e .
bioagent run --tier precision --model antibody-design "design thermostable anti-HA broadly neutralizing antibody"
```

---

## Model & compute requirements

| Component | Underlying Model | Typical VRAM | Latency (per task) |
|-----------|------------------|--------------|-------------------|
| DNA variant effect prediction | DNABERT‑2 | 8 GB | < 100 ms |
| PPI prediction (host‑virus) | SEHI‑PPI | 6 GB | < 1.5 s |
| Protein binding affinity | ESM‑2 650M | 16 GB | ~2 min |
| Base LLM (RAG / synthesis) | Ollama‑served BioT5+ 7B | 16 GB | depends on prompt length |
| Full pipeline (question → designed sequence) | multi‑container orchestration | 24 GB (L40S) | < 30 s (excl. literature search) |

All models run **locally**. No cloud API calls. No telemetry.

---

## Tier & partner registry

| Tier | Package | Domain | Status |
|------|---------|--------|--------|
| Foundation | `bioagent-tier1-foundation` | BioT5+ base model, MLOps, domain corpus | alpha |
| Precision | `bioagent-tier2-precision` | DNA‑LM, PPI, protein‑LM inference | alpha |
| Fusion | `bioagent-tier3-fusion` | Multi‑omics ETL, Neo4j knowledge graph | planned |
| Strategy | `bioagent-tier4-strategy` | Grant writing, budgeting, compliance reports | planned |

Active lab partners: **2 influenza/immunology laboratories in Montreal** (Phase 1 MVP, on‑going).

---

## Active learning flywheel

1. **Hypothesis generation** – the hypothesis engine scans knowledge graph gaps and proposes testable statements (e.g., *“HA stalk mutation A22T is predicted to disrupt ANP32A binding”*).
2. **Wet‑lab feedback** – researchers upload experimental results (SPR, growth curves) via the hypothesis panel and mark each hypothesis as *supported* or *refuted*.
3. **Auto fine‑tuning** – the loop manager detects sufficient new verified data and triggers QLoRA fine‑tuning of the relevant base model.
4. **Canary deployment** – the new adapter is deployed in A/B test mode; once accuracy improves, it is promoted to the production model.
5. **Full lineage** – every step is recorded in the L0 audit trail, ready for ethics committee review and manuscript methods sections.

---

## Deployment

### Local development
```bash
pip install -e ".[dev]"
pytest tests/                # unit tests
pytest -m integration        # requires local model containers
```

### Docker (recommended for labs)
```bash
cp .env.example .env
docker compose up            # UI :7860, ChromaDB :8001, Ollama :11434
```

### Privacy & compliance
- **All data stays on the lab machine.** No telemetry. No cloud vector store.
- **L0 audit layer** generates hardware isolation proofs (TPM‑backed) and Loi 25 self‑assessment reports.
- **Built‑in PII de‑identification** and optional sequence IP screening (MMseqs2) – the lab controls everything.

---

## Contributing

- **Core framework**: open PRs to this repo
- **New Tier‑2 model containers**: create a `bioagent-tier2-<name>` package and register it in the Model Zoo
- **New ETL adapters (Tier‑3)** or **compliance templates (L0)**: follow the contributor guide

See [CONTRIBUTING.md](CONTRIBUTING.md) for coding standards and the Tier manifest specification.

---

## License

The BioAgent core framework (`bioagent`) is **MIT licensed**.

Official tier packages (`bioagent-tier2-*` etc.) are **CC BY‑NC 4.0**: free for academic and non‑profit research, commercial use requires a separate agreement. See individual package repositories for details.

---

## Citation

If you use BioAgent in your research, please cite:

```bibtex
@software{bioagent2026,
  author  = {BioAgent Team},
  title   = {BioAgent: On-premises multimodal molecular intelligence platform for biomedical research partnerships},
  year    = {2026},
  url     = {https://github.com/your-org/bioagent},
}
```
```