# FluBroad Skill Specification

**Version 1.0 | 2026**

This document is the authoritative specification for FluBroad Skill packages. If you want to build a Skill for a new biomedical domain — oncology, immunology, neuroscience — this is the complete reference.

---

## Table of contents

1. [What is a Skill?](#1-what-is-a-skill)
2. [Package structure](#2-package-structure)
3. [SkillManifest fields](#3-skillmanifest-fields)
4. [Writing agents](#4-writing-agents)
5. [Entry point registration](#5-entry-point-registration)
6. [Section queries and instructions](#6-section-queries-and-instructions)
7. [Extraction schema](#7-extraction-schema)
8. [Knowledge graph config](#8-knowledge-graph-config)
9. [Grant templates](#9-grant-templates)
10. [Fine-tuning config](#10-fine-tuning-config)
11. [Testing your Skill](#11-testing-your-skill)
12. [Publishing](#12-publishing)

---

## 1. What is a Skill?

A Skill is a Python package that extends FluBroad for a specific biomedical domain. It contains:

- **Data agents** — adapters for domain-relevant databases
- **SkillManifest** — a declarative configuration object that tells the FluBroad orchestrator how to behave for this domain
- **Domain knowledge** — prompt templates, entity schemas, entity-extraction patterns

The framework provides the infrastructure. The Skill provides the expertise.

```
User: "KRAS G12C NSCLC sotorasib resistance mechanisms"
   │
   ├── SkillLoader.load("oncology")           ← your Skill
   │   └── manifest.agents = ["pubmed", "tcga", "clinicaltrials", ...]
   │   └── manifest.section_queries = {...}
   │   └── manifest.extraction_schema = mutation_schema
   │
   └── FluBroadOrchestrator(config, skill=skill)
         ← framework handles RAG, PPT, graph, QA, everything else
```

---

## 2. Package structure

Use `flubroad new-skill <name>` to scaffold. Manual structure:

```
flubroad-skill-<domain>/
│
├── <domain>/                           # main Python package
│   ├── __init__.py
│   ├── skill.py                        # SkillManifest declaration  ← REQUIRED
│   ├── config.py                       # Pydantic settings (optional)
│   └── agents/                         # domain data agents
│       ├── __init__.py
│       ├── tcga_agent.py               # example: TCGA adapter
│       └── cosmic_agent.py             # example: COSMIC mutations
│
├── domain/<domain>/                    # domain knowledge
│   ├── schemas/
│   │   └── entity_schema.py            # extraction schema
│   └── prompts/
│       ├── section_queries.py          # RAG retrieval queries
│       ├── section_instructions.py     # LLM synthesis prompts
│       └── grant_templates.py          # grant mode (optional)
│
├── tests/
│   ├── test_agents.py                  # no live API calls
│   └── test_skill_manifest.py
│
├── pyproject.toml                      # entry points  ← REQUIRED
├── README.md
└── LICENSE                             # CC BY-NC 4.0 recommended
```

---

## 3. SkillManifest fields

Full reference for all fields in `flubroad.skill.SkillManifest`.

### Required fields

#### `name: str`
Short machine-readable identifier. Globally unique across the Skill ecosystem.

```python
name = "oncology"
```

Rules:
- Lowercase letters, numbers, hyphens only
- No spaces
- Must match the entry point key in `pyproject.toml`

#### `version: str`
Semantic version. Increment the minor version for new agents or sections; patch for bug fixes; major for breaking schema changes.

```python
version = "1.0.0"
```

#### `display_name: str`
Human-readable name shown in the UI, logs, and Skill registry.

```python
display_name = "FluBroad Oncology: KRAS, EGFR & targeted therapy"
```

#### `agents: List[str]`
Agent keys this Skill provides (and optionally uses by default). Every key must be registered as a `flubroad.agents` entry point.

```python
agents = ["pubmed", "europe_pmc", "tcga", "clinicaltrials", "cosmic", "depmap"]
```

#### `section_queries: Dict[str, str]`
RAG retrieval queries sent to the vector store, one per review section. These are keyword-dense strings optimised for semantic search, not natural language questions.

```python
section_queries = {
    "problem":    "KRAS mutation NSCLC treatment resistance prevalence incidence",
    "motivation": "RAS GTPase KRAS G12C covalent inhibitor targeting strategy",
    "results":    "sotorasib adagrasib KRAS G12C clinical trial ORR PFS OS",
    "mechanisms": "KRAS G12C inhibitor resistance bypass pathway SOS1 EGFR",
    "challenges": "adaptive resistance immunotherapy combination KRAS inhibitor",
    "future":     "pan-RAS inhibitor PROTAC degrader next generation KRAS",
}
```

#### `section_instructions: Dict[str, str]`
LLM prompts for synthesis, one per section. Keys must match `section_queries`.

Requirements for each instruction:
- State the word count target (150–400 words per section)
- Mandate `[PMID]` citation for every factual claim
- Specify what to compare or contrast
- Forbid vague statements ("further research is needed")

```python
section_instructions = {
    "results": (
        "Write the 'Key Results' section.\n"
        "- Compare sotorasib, adagrasib, and at least 2 other KRAS G12C inhibitors.\n"
        "- Include: drug name, ORR, PFS, OS, trial phase, patient population.\n"
        "- Note resistance mechanisms observed in each trial.\n"
        "- Every claim MUST include a PMID. Length: 300–400 words. No header."
    ),
    ...
}
```

#### `extraction_schema: Dict[str, Any]`
JSON schema for structured entity extraction by the LLM after synthesis. The schema defines the primary entity type for this domain.

```python
extraction_schema = {
    "type": "object",
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "drug_name":       {"type": "string"},
                    "target":          {"type": "string"},
                    "mutation":        {"type": "string"},
                    "cancer_type":     {"type": "string"},
                    "clinical_phase":  {"type": "string"},
                    "orr":             {"type": "string"},
                    "key_pmids":       {"type": "array", "items": {"type": "string"}},
                },
                "required": ["drug_name", "target"],
            },
        }
    },
}
```

---

### Recommended fields

#### `description: str`
One paragraph. Appears in the Skill registry, PyPI, and `flubroad list-skills`.

#### `topic_keywords: List[str]`
Used to filter corpus items for relevance (Jaccard bag-of-words). 10–30 words recommended. Include synonyms, gene names, disease abbreviations.

```python
topic_keywords = [
    "kras", "nsclc", "lung cancer", "ras", "raf", "mapk",
    "sotorasib", "adagrasib", "amg510", "egfr", "alk",
    "targeted therapy", "immunotherapy", "resistance",
]
```

#### `system_prompt: str`
LLM system message. Establish the domain expert persona. If omitted, a generic message is generated from `display_name`.

```python
system_prompt = (
    "You are a senior oncologist specialising in RAS-driven cancers. "
    "Write rigorous, evidence-based synthesis sections. "
    "Cite every factual claim with a PMID. Be analytical, not descriptive."
)
```

---

### Optional fields

#### `default_agents: List[str]`
Subset of `agents` used when the user does not pass `--agents`. Defaults to all agents. Set this to the 4–6 most productive agents to keep default runs fast.

```python
default_agents = ["pubmed", "europe_pmc", "clinicaltrials", "cosmic"]
```

#### `grant_templates: Dict[str, str]`
Section instructions for grant-writing mode. If empty, `section_instructions` is used. Keys: same as `section_queries` plus "specific_aims", "research_strategy".

#### `knowledge_graph_config: Dict[str, Any]`
Configures entity extraction patterns for `FluBroadGraph`. If empty, generic patterns are used.

```python
knowledge_graph_config = {
    "node_types": {
        "Drug":       "Drug",
        "Mutation":   "Mutation",
        "Cancer":     "Cancer",
        "Gene":       "Gene",
        "Publication": "Publication",
    },
    "edge_types": {
        "TARGETS":    "Drug → Gene",
        "ASSOCIATED": "Mutation → Cancer",
        "CITED_IN":   "Drug → Publication",
    },
    "entity_patterns": {
        "drug":     r"\b(sotorasib|adagrasib|AMG\s?510|MRTX\s?849)\b",
        "mutation": r"\b(KRAS\s?G12[CDVRA]|EGFR\s?ex\d+)\b",
        "gene":     r"\b(KRAS|NRAS|HRAS|BRAF|RAF1|MEK1|MEK2|ERK)\b",
    },
}
```

#### `output_section_order: List[str]`
Order of sections in the final report. Defaults to `list(section_queries.keys())`.

#### `output_section_titles: Dict[str, str]`
Display titles used in PPT, Word doc, and UI.

```python
output_section_titles = {
    "problem":    "Clinical Challenge",
    "motivation": "Rationale for KRAS Targeting",
    "results":    "Key Clinical Results",
    "mechanisms": "Resistance Mechanisms",
    "challenges": "Unsolved Problems",
    "future":     "Next-Generation Strategies",
}
```

#### `finetuning_config: Dict[str, Any]`
```python
finetuning_config = {
    "base_model":             "unsloth/llama-3-8b-Instruct",
    "lora_rank":              16,
    "feedback_dir":           "data/feedback",
    "min_examples_to_train":  50,
    "export_format":          "sharegpt",
}
```

#### `chart_config: Dict[str, Any]`
```python
chart_config = {
    "trend_chart":          True,    # publication volume over time
    "heatmap_source_agent": "",      # agent key for heatmap data (or "")
    "custom_charts":        [],      # list of custom chart functions (advanced)
}
```

---

## 4. Writing agents

Agents inherit from `flubroad.agents.BaseAgent`:

```python
# oncology/agents/tcga_agent.py
from flubroad.agents.base import AgentConfig, BaseAgent, FetchResult
import asyncio
import requests

class TCGAAgent(BaseAgent):
    def get_capabilities(self) -> list[str]:
        return ["mutation", "expression", "survival", "tcga"]

    def get_default_prompt(self) -> str:
        return (
            "You are an oncologist. Based on these TCGA records about {topic}, "
            "describe mutation frequencies, co-occurrence patterns, and survival impact."
        )

    async def fetch(self, query: str, limit: int = 100, **kwargs) -> FetchResult:
        items = await asyncio.to_thread(self._query_tcga, query, limit)
        return FetchResult(
            source=self.name,
            items=items,
            metadata={"total": len(items), "query": query},
            prompt_context=self._build_context(items),
        )

    def _query_tcga(self, query: str, limit: int) -> list[dict]:
        # your implementation here
        ...
```

Rules:
- `fetch()` must be `async`. Use `asyncio.to_thread()` for sync HTTP calls.
- Every item dict must include: `source`, `title`, `abstract`, `pmid` (or empty string), `year`, `citation_count`, `fulltext_available`.
- Print `[AgentName] N items` for logging.
- Never raise exceptions from `fetch()` — catch and return empty list with a print.

---

## 5. Entry point registration

```toml
# pyproject.toml

[project.entry-points."flubroad.skills"]
oncology = "oncology.skill:manifest"       # key = Skill name

[project.entry-points."flubroad.agents"]
tcga    = "oncology.agents.tcga_agent:TCGAAgent"
cosmic  = "oncology.agents.cosmic_agent:COSMICAgent"
depmap  = "oncology.agents.depmap_agent:DepMapAgent"
# pubmed, europe_pmc, etc. are provided by the framework — don't re-register
```

After `pip install -e .`:
```bash
flubroad list-skills    # should show: oncology (0.1.0)
flubroad list-agents    # should show your new agents
```

---

## 6. Section queries and instructions

### Queries
- 8–15 words. Dense keywords, not sentences.
- Include synonyms of the central concept.
- Different sections should use different vocabulary to retrieve different chunks.

### Instructions
- Open with the section name: "Write the 'Results' section."
- Specify exact content requirements (minimum entities to compare, statistics to include).
- Always: "Every claim MUST include a PMID."
- Always: "Length: NNN–MMM words. No header."
- Forbid vague closings: "Avoid 'further research is needed'."

### Testing your prompts
```bash
flubroad run --skill oncology --sections results "KRAS G12C NSCLC sotorasib"
```

---

## 7. Extraction schema

The schema is passed verbatim to the LLM with the instruction:
> "Extract all [entity type] mentioned in the text. Return JSON: {entities: [...]}."

Design guidelines:
- Keep required fields to the 3–5 most important
- Use string types for everything (numbers come back inconsistently from LLMs)
- Include `key_pmids: array of strings` in every entity — this links entities to the knowledge graph
- Name the array field `entities` for framework compatibility

---

## 8. Knowledge graph config

The `entity_patterns` dict maps node type names to regex patterns. These run against title + abstract for every corpus item.

```python
"entity_patterns": {
    "drug":     r"\b(sotorasib|adagrasib|AMG\s?510)\b",
    "mutation": r"\b(KRAS\s?G12[CDVRA])\b",
}
```

Pattern tips:
- Use `\b` word boundaries
- Allow optional whitespace with `\s?`
- List the 10–20 most important named entities, not generic terms
- Keep patterns specific — overly broad patterns create noisy graphs

---

## 9. Grant templates

```python
grant_templates = {
    "specific_aims": (
        "Write a 1-page NIH Specific Aims section.\n"
        "- Opening paragraph: clinical problem and gap (2 sentences).\n"
        "- Aim 1, 2, 3: each with a testable hypothesis and expected outcome.\n"
        "- Closing: impact statement.\n"
        "Cite every factual claim with [PMID]. ~450 words."
    ),
    "significance": (
        "Write the 'Significance' section of an NIH Research Strategy.\n"
        "- Describe the clinical and scientific gap this project addresses.\n"
        "- Quantify the problem (incidence, mortality, unmet need).\n"
        "- Explain how this work advances the field.\n"
        "Cite every claim with [PMID]. ~400 words."
    ),
}
```

---

## 10. Fine-tuning config

```python
finetuning_config = {
    "base_model":             "unsloth/llama-3-8b-Instruct",   # HF model ID
    "lora_rank":              16,       # 8 for small datasets, 32 for rich
    "lora_alpha":             16,       # usually equal to rank
    "feedback_dir":           "data/feedback",
    "min_examples_to_train":  50,       # warn if fewer
    "export_format":          "sharegpt",   # or "alpaca"
    "hf_repo":                "",       # push to HF after training (optional)
}
```

Feedback is collected automatically via the Gradio "Expert Feedback" tab. Export with:
```bash
flubroad export-feedback --skill oncology --output data/train.jsonl
python scripts/finetune_lora.py --data data/train.jsonl
```

---

## 11. Testing your Skill

```bash
# Validate the manifest (no network required)
pytest tests/test_skill_manifest.py -v

# Test agents with mocked HTTP
pytest tests/test_agents.py -v

# Integration test (requires API access, slow)
pytest -m integration tests/test_agents.py -v
```

Minimum test coverage required for registry listing:

```python
# tests/test_skill_manifest.py
from flubroad.skill import SkillManifest, SkillLoader
from oncology.skill import manifest

def test_manifest_type():
    assert isinstance(manifest, SkillManifest)

def test_required_fields():
    assert manifest.name
    assert manifest.version
    assert manifest.agents
    assert manifest.section_queries
    assert manifest.section_instructions
    assert manifest.extraction_schema

def test_sections_consistent():
    assert set(manifest.section_queries.keys()) == set(manifest.section_instructions.keys())

def test_agents_registered():
    # Verifies entry points are wired up
    from flubroad.agents.registry import AgentRegistry
    AgentRegistry.load_plugins()
    for agent_name in manifest.agents:
        assert agent_name in AgentRegistry.available(), \
            f"Agent '{agent_name}' not registered"
```

---

## 12. Publishing

### Name your package
```
flubroad-skill-<domain>
```

### PyPI
```bash
pip install build
python -m build
twine upload dist/*
```

### Submit to the registry
Open a PR to [flubroad](https://github.com/yiweixidu/flubroad) adding your Skill to the registry table in `README.md`:

```markdown
| `oncology` | `flubroad-skill-oncology` | Cancer genomics, targeted therapy | @yourhandle | stable |
```

### License
Academic Skills: **CC BY-NC 4.0** (matches the official Skill license model)
Fully open Skills: **MIT**

---

*Questions? Open an issue at [github.com/yiweixidu/flubroad](https://github.com/yiweixidu/flubroad).*
