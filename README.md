# FluBroad Agent Framework

> Build biomedical AI agents once. Extend to any discipline with a Skill package.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/flubroad.svg)](https://pypi.org/project/flubroad/)

FluBroad is an open-source framework for building domain-specific biomedical AI agents. It provides a complete pipeline — multi-source data fetching, RAG indexing, LLM synthesis, knowledge graph, Q&A, and document generation — as reusable infrastructure. Domain expertise lives in **Skill packages** that plug into the framework without touching the core.

```
pip install flubroad
pip install flubroad-skill-virology     # BioVoice: bnAb & influenza research
pip install flubroad-skill-oncology     # coming soon
pip install flubroad-skill-immunology   # coming soon
```

---

## The problem this solves

Every biomedical lab building an AI research assistant writes the same code: fetch from PubMed, chunk abstracts, embed into a vector store, call an LLM, format a slide deck. The domain knowledge — which databases matter, how to extract entities, which prompt templates work — is different per discipline but the plumbing is identical.

FluBroad separates the two:

| Layer | What it contains | Who writes it |
|-------|-----------------|---------------|
| **Framework** (`flubroad`) | Fetch, RAG, synthesis, PPT, video, Q&A, graph, fine-tuning loop | Framework team |
| **Skill** (`flubroad-skill-*`) | Prompt templates, extraction schemas, database adapters, entity patterns | Domain experts |

A virologist writes a 50-line `SkillManifest`. The framework handles the rest.

---

## Quickstart

### With an existing Skill

```bash
pip install flubroad flubroad-skill-virology

cp .env.example .env    # set OPENAI_API_KEY or LLM_TYPE=ollama

flubroad run \
  --skill virology \
  "broadly neutralizing antibodies influenza hemagglutinin"
```

Output in `./output/`:
- `review.docx` — cited literature review
- `slides.pptx` — presentation deck with data visualisations
- `knowledge_graph.graphml` — antibody-epitope-publication graph
- `video.mp4` — narrated walkthrough (optional)

### Fully local (zero API cost)

```bash
flubroad run --skill virology --llm ollama/llama3.1:8b "your query"
```

### Docker (one command)

```bash
docker compose up     # starts at http://localhost:7860
```

---

## Architecture

```
User query
    │
    ├── SkillLoader.load("virology")      ← loads SkillManifest
    │
    ├── [parallel asyncio.gather]
    │     └── agents from skill.agents[]  ← data fetching
    │
    ├── Merge + deduplicate by PMID/DOI
    │   Rank: recency × citations × domain Jaccard
    │
    ├── RAG index  (Chroma + BAAI/bge-small, CPU)
    │
    ├── Section synthesis  (LLM)
    │   Queries + instructions from skill.section_queries / section_instructions
    │   Every claim: [PMID] — suspicious citations flagged
    │
    ├── Knowledge graph  (NetworkX)
    │   Entities + patterns from skill.knowledge_graph_config
    │
    └── Output pipeline
          ├── Word doc   (python-docx)
          ├── PPT slides (python-pptx + matplotlib charts)
          └── Video      (edge-tts + moviepy)
```

```
flubroad/
├── agents/
│   ├── base.py            # BaseAgent, AgentConfig, FetchResult
│   └── registry.py        # AgentRegistry — loads agents via entry points
├── core/
│   ├── orchestrator.py    # FluBroadOrchestrator — Skill-aware pipeline
│   ├── task.py            # Task state machine
│   └── skill_loader.py    # SkillLoader — discovers installed Skills
├── skill.py               # SkillManifest dataclass (the Skill contract)
├── models/                # ModelClient — OpenAI + Ollama abstraction
├── rag/                   # Chroma RAG (vector store + retrieval)
├── output/                # PPTGenerator, Word, Video renderers
├── knowledge_graph/       # FluBroadGraph (NetworkX MultiDiGraph)
├── qa/                    # QAEngine — multi-turn RAG Q&A
└── finetuning/            # FeedbackStore + LoRA export (ShareGPT/Alpaca)
```

---

## The Skill interface

A Skill package is a Python package that:

1. Implements one or more `BaseAgent` subclasses (data sources)
2. Declares a `SkillManifest` instance
3. Registers everything via `pyproject.toml` entry points

```python
# myskill/skill.py
from flubroad.skill import SkillManifest

manifest = SkillManifest(
    name="virology",
    version="1.0.0",
    display_name="BioVoice: Virology & Broadly Neutralizing Antibodies",
    description="...",
    agents=["pubmed", "europe_pmc", "pdb", "uniprot", ...],
    section_queries={
        "results": "broadly neutralizing antibody IC50 neutralization spectrum",
        "mechanisms": "Fc effector function ADCC broadly neutralizing antibody",
        ...
    },
    section_instructions={
        "results": "Compare at least 4 specific bnAbs...",
        ...
    },
    extraction_schema=my_entity_schema,
    topic_keywords=["influenza", "hemagglutinin", "bnab", ...],
)
```

```toml
# pyproject.toml
[project.entry-points."flubroad.skills"]
virology = "myskill.skill:manifest"

[project.entry-points."flubroad.agents"]
pubmed   = "myskill.agents.pubmed_agent:PubMedAgent"
pdb      = "myskill.agents.pdb_agent:PDBAgent"
```

Full specification: [docs/skill-spec.md](docs/skill-spec.md)

---

## Building a new Skill

```bash
pip install flubroad[dev]
flubroad new-skill oncology    # scaffolds a new Skill package
```

The scaffold creates:

```
flubroad-skill-oncology/
├── oncology/
│   ├── agents/
│   │   ├── base_adapters.py   # inherit from flubroad.agents.BaseAgent
│   │   └── tcga_agent.py      # example: TCGA data adapter
│   ├── skill.py               # SkillManifest declaration
│   └── config.py              # OncologySettings
├── domain/oncology/
│   ├── schemas/               # entity extraction schemas
│   └── prompts/               # section queries + instructions
├── tests/
└── pyproject.toml
```

Then:

```bash
cd flubroad-skill-oncology
pip install -e .
flubroad run --skill oncology "KRAS G12C NSCLC targeted therapy"
```

---

## LLM options

| Flag | Provider | Cost | Notes |
|------|----------|------|-------|
| `--llm openai/gpt-4o-mini` | OpenAI | ~$0.05/run | Default |
| `--llm openai/gpt-4o` | OpenAI | ~$0.50/run | Higher quality |
| `--llm ollama/llama3.1:8b` | Local | Free | Requires [Ollama](https://ollama.ai) |
| `--llm ollama/llama3.2:3b` | Local | Free | Fast, lower quality |

All Skill output quality scales with the model. For grant writing, use `gpt-4o`.

---

## Skill registry

| Skill | Package | Domain | Maintainer | Status |
|-------|---------|--------|------------|--------|
| `virology` | `flubroad-skill-virology` | Influenza, bnAbs, vaccine design | [@yiweixidu](https://github.com/yiweixidu) | stable |
| `oncology` | `flubroad-skill-oncology` | Cancer genomics, targeted therapy | — | planned |
| `immunology` | `flubroad-skill-immunology` | TCR/BCR repertoire, immune evasion | — | planned |

Want to add a Skill? See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Data flywheel

Every Skill package ships with a built-in feedback loop:

1. Expert reviews generated output in the Gradio UI ("Expert Feedback" tab)
2. `FeedbackStore` logs the correction with a quality rating
3. `FeedbackStore.export_jsonl()` exports ShareGPT-format training data
4. `scripts/finetune_lora.py` fine-tunes a domain LoRA adapter (Unsloth, 1 GPU)
5. LoRA weights pushed to Hugging Face under `flubroad-skill-*/`
6. Next user gets a better model — loop closes

```bash
# Export feedback and fine-tune
flubroad export-feedback --skill virology --output data/train.jsonl
python scripts/finetune_lora.py --data data/train.jsonl --model unsloth/llama-3-8b-Instruct
```

---

## Deployment

### Local dev
```bash
pip install -e ".[dev]"
pytest tests/                   # unit tests, no API calls
pytest -m integration           # requires NCBI API access
```

### Docker (recommended for labs)
```bash
cp .env.example .env
docker compose up               # Gradio at :7860, ChromaDB at :8001
docker compose --profile ollama up   # adds local Ollama at :11434
```

### Privacy
All data stays on your machine. No telemetry. No cloud vector store. ChromaDB runs in-process or as a local container. Ollama option requires zero external API calls.

---

## Contributing

- Core framework: open PRs to this repo
- New Skills: create `flubroad-skill-<domain>` and open a PR to add it to the registry above
- Existing Skills: open PRs to the relevant Skill repo

See [CONTRIBUTING.md](CONTRIBUTING.md) for standards, the Skill SDK, and the review process.

---

## License

The FluBroad core framework is **MIT licensed**.

Official Skill packages (`flubroad-skill-*`) use **CC BY-NC 4.0**: free for academic use, commercial use requires a license. See individual Skill repos for details.

---

## Citation

If you use FluBroad in research, please cite:

```bibtex
@software{flubroad2026,
  author  = {Xidu, Yiwei},
  title   = {FluBroad Agent Framework: Open-source infrastructure for biomedical AI agents},
  year    = {2026},
  url     = {https://github.com/yiweixidu/flubroad},
}
```
