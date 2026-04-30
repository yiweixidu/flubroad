# BioAgent Tier Package Specification

**Version 1.0 | 2026**

This document is the authoritative specification for BioAgent **tier packages** — installable Python packages that extend the BioAgent platform with dedicated model containers, ETL adapters, compliance templates, or other components that realize the four‑tier commercial architecture. If you want to build a new molecular intelligence module, multi‑omics data pipeline, or grant‑writing template, this is the complete reference.

---

## Table of contents

1. [What is a Tier package?](#1-what-is-a-tier-package)
2. [Package structure](#2-package-structure)
3. [TierManifest fields](#3-tiermanifest-fields)
4. [Writing model containers](#4-writing-model-containers)
5. [Writing ETL adapters](#5-writing-etl-adapters)
6. [Writing compliance templates](#6-writing-compliance-templates)
7. [Entry point registration](#7-entry-point-registration)
8. [Container API reference](#8-container-api-reference)
9. [Testing your tier package](#9-testing-your-tier-package)
10. [Publishing](#10-publishing)

---

## 1. What is a Tier package?

A **tier package** is a Python package that implements one or more components belonging to one of BioAgent’s four commercial tiers (Foundation, Precision, Fusion, Strategy) or the horizontal support layer. It contains:

- **Model containers** — Docker‑ready inference microservices wrapping DNA/protein language models, PPI predictors, or molecular generators.
- **ETL adapters** — data pipelines that load, transform, and store multi‑omics raw files into the unified data lake.
- **Compliance templates** — Loi 25 / GDPR / HIPAA self‑assessment report generators.
- **Grant‑writing assets** — funder‑specific RAG templates, budget calculators, milestone trackers.
- **A manifest** — a declarative `TierManifest` that tells the BioAgent orchestrator what the package provides, what hardware it requires, and how to integrate it.

The BioAgent framework provides the orchestration, zero‑trust audit plane, model zoo registry, and user interface. The tier package provides the domain‑specific molecular or data capabilities.

```
User query: "Design a thermostable H5N1 HA stalk antibody"
   │
   ├── TierLoader.load(["precision", "strategy"])   ← loads manifests
   │
   ├── [L2.5 Model Zoo]
   │     ├── Protein generation container (ProtGPT2)
   │     ├── Binding affinity container (ESM‑2)
   │     └── Antibody virtual screening container
   │
   ├── [L4 Knowledge Layer]
   │     └── Grant RAG pipeline (Tier 4)
   │
   └── BioAgentOrchestrator(config, tiers=[...])
         ← framework handles orchestration, audit, UI, output
```

---

## 2. Package structure

Use `bioagent new-tier <name>` to scaffold. Manual structure:

```
bioagent-tier2-<name>/
│
├── <tier_name>/                         # main Python package
│   ├── __init__.py
│   ├── manifest.py                      # TierManifest declaration  ← REQUIRED
│   ├── config.py                        # Pydantic settings (optional)
│   ├── containers/                      # model containers (for Tier 2)
│   │   ├── __init__.py
│   │   ├── dna_lm.py
│   │   └── ppi.py
│   ├── etl/                             # ETL adapters (for Tier 3)
│   │   ├── fastq_loader.py
│   │   └── elisa_loader.py
│   └── templates/                       # grant/compliance templates (Tier 4/L0)
│       ├── loi25_report.py
│       └── nserc_budget.py
│
├── tests/
│   ├── test_containers.py               # mock inference tests
│   ├── test_etl.py
│   └── test_manifest.py
│
├── pyproject.toml                       # entry points  ← REQUIRED
├── README.md
└── LICENSE                              # CC BY‑NC 4.0 recommended
```

---

## 3. TierManifest fields

Full reference for all fields in `bioagent.core.tier.TierManifest`.

### Required fields

#### `name: str`
Short machine‑readable identifier. Must be unique among installed tier packages.

```python
name = "precision-dna-lm"
```

Rules:
- Lowercase letters, numbers, hyphens only
- No spaces
- Must match the entry point key in `pyproject.toml`

#### `version: str`
Semantic version.

```python
version = "1.0.0"
```

#### `tier: str`
Which tier this package belongs to: `"foundation"`, `"precision"`, `"fusion"`, `"strategy"`, or `"horizontal"`.

```python
tier = "precision"
```

#### `display_name: str`
Human‑readable name shown in the UI and logs.

```python
display_name = "DNA Language Model – Variant Effect Prediction"
```

#### `provides: List[str]`
List of component types provided by this package. Allowed values: `"model_container"`, `"etl_adapter"`, `"compliance_template"`, `"grant_template"`, `"hypothesis_engine"`, `"feedback_loop"`.

```python
provides = ["model_container"]
```

---

### Model container specific

If `"model_container"` is in `provides`, the following fields are required:

#### `containers: Dict[str, str]`
Mapping from container short name to Python object path.

```python
containers = {
    "dna-language-model": "precision_dna_lm.containers.dna_lm:DNALanguageModelContainer",
    "ppi-predictor": "precision_dna_lm.containers.ppi:PPIPredictorContainer",
}
```

#### `models: Dict[str, Dict[str, Any]]`
Metadata for each container, including model architecture, parameter count, typical VRAM, and Docker image.

```python
models = {
    "dna-language-model": {
        "architecture": "DNABERT-2",
        "parameters": "110M",
        "min_vram_gb": 8,
        "docker_image": "bioagent/dnabert2:v1.0",
        "input_schema": "path/to/input_schema.json",  # optional
        "output_schema": "path/to/output_schema.json", # optional
    },
}
```

#### `requires_gpu: bool`
Whether the containers require a GPU. Default `True`.

```python
requires_gpu = True
```

---

### ETL adapter specific

If `"etl_adapter"` is in `provides`:

#### `etl_adapters: Dict[str, str]`
Mapping from adapter name to class path.

```python
etl_adapters = {
    "fastq-loader": "tier3_fusion.etl.fastq:FastqLoader",
    "elisa-loader": "tier3_fusion.etl.elisa:ELISALoader",
}
```

#### `supported_formats: Dict[str, List[str]]`
File formats each adapter can handle.

```python
supported_formats = {
    "fastq-loader": ["fastq", "fastq.gz"],
    "elisa-loader": ["csv", "xlsx"],
}
```

---

### Recommended fields

#### `description: str`
One‑paragraph description used in the tier registry and `bioagent list-tiers`.

#### `hardware_requirements: Dict[str, Any]`
Minimal hardware needed.

```python
hardware_requirements = {
    "gpu": "NVIDIA L40S or A10",
    "vram": "24 GB",
    "ram": "64 GB",
    "disk": "500 GB SSD",
}
```

#### `docker_compose_fragment: str`
Path to a Docker Compose snippet that adds the package’s services to the local deployment.

```python
docker_compose_fragment = "docker-compose.tier2.yml"
```

---

### Optional fields

#### `horizontals: Dict[str, Any]`
If the package provides horizontal components like a hypothesis engine or compliance template.

```python
horizontals = {
    "hypothesis_engines": {
        "binding-disruption": "horizontal.engines.binding:BindingDisruptionEngine",
    },
}
```

#### `compliance_templates: Dict[str, str]`
```python
compliance_templates = {
    "loi25-full": "horizontal.compliance.loi25:generate_report",
}
```

---

## 4. Writing model containers

Model containers inherit from `bioagent.model_zoo.base.BaseModelContainer`:

```python
# precision_dna_lm/containers/dna_lm.py
from bioagent.model_zoo.base import BaseModelContainer
from typing import Any, Dict

class DNALanguageModelContainer(BaseModelContainer):
    def __init__(self):
        super().__init__(
            model_name="dna-language-model",
            version="1.0.0"
        )
        # Load model weights here (lazy or in __init__)

    async def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        input_data: {"sequence": "ATCG...", "coordinates": "chr11:534289"}
        Returns: {"variant_effect": 0.87, "interpretation": "...", "confidence": 0.93, "evidence": [...]}
        """
        ...

    def health(self) -> bool:
        """Return True if model is loaded and responsive."""
        ...

    def metadata(self) -> Dict[str, Any]:
        return {
            "architecture": "DNABERT-2",
            "training_data": "1000 Genomes + ENCODE",
            "parameters": "110M",
            "license": "CC BY-NC 4.0",
        }
```

Rules:
- `predict()` must be `async` and never raise exceptions; return an error dict instead.
- Every return dict from `predict` must contain the keys `"result"` and `"provenance"` (list of citations/PDB IDs).
- Implement `health()` to be used by the orchestration health check.
- `metadata()` must include `architecture`, `training_data`, `parameters`, and `license`.

---

## 5. Writing ETL adapters

ETL adapters inherit from `bioagent.data.BaseLoader`:

```python
# tier3_fusion/etl/fastq.py
from bioagent.data import BaseLoader, Study, Assay
import asyncio

class FastqLoader(BaseLoader):
    def __init__(self):
        super().__init__(format="fastq")

    async def load(self, file_path: str) -> list[Study]:
        # Parse FASTQ, extract metadata
        ...
        return [study_obj]

    async def transform(self, studies: list[Study]) -> list[Study]:
        # Normalize metadata, add ontology terms
        ...
        return studies

    async def store(self, studies: list[Study]):
        # Write to the experiment store (L3)
        ...
```

---

## 6. Writing compliance templates

A compliance template is a callable that generates a self‑assessment report. It relies on the L0 audit layer for lineage data.

```python
# horizontal/compliance/loi25.py
def generate_report(audit_trail: dict) -> str:
    """
    audit_trail: data from L0 audit plane
    Returns markdown report
    """
    ...
    return report_md
```

---

## 7. Entry point registration

```toml
# pyproject.toml
[project.entry-points."bioagent.tiers"]
precision-dna-lm = "precision_dna_lm.manifest:manifest"
```

After installation:
```bash
bioagent list-tiers          # shows precision-dna-lm (0.1.0)
bioagent list-containers     # shows dna-language-model, ppi-predictor
```

---

## 8. Container API reference

Every model container must expose a standardized HTTP API when deployed via the gateway. The L2.5 Model Zoo auto‑generates these endpoints:

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/predict/{container_name}` | Run inference |
| `GET`  | `/health/{container_name}` | Container health |
| `GET`  | `/metadata/{container_name}` | Model info |

Predict request body (JSON):
```json
{
    "input": { ... },
    "parameters": { "temperature": 0.1 }
}
```

Predict response:
```json
{
    "result": { ... },
    "provenance": [{"source": "PDB:1ABC", "description": "..."}],
    "confidence": 0.95,
    "audit": { "request_id": "...", "timestamp": "..." }
}
```

---

## 9. Testing your tier package

```bash
# Validate manifest (no GPU needed)
pytest tests/test_manifest.py -v

# Test containers with mock model
pytest tests/test_containers.py -v

# Integration test (requires GPU + model weights)
pytest -m integration tests/test_containers.py -v
```

Minimum test coverage for the tier registry:

```python
# tests/test_manifest.py
from bioagent.core.tier import TierManifest
from precision_dna_lm.manifest import manifest

def test_manifest_type():
    assert isinstance(manifest, TierManifest)

def test_required_fields():
    assert manifest.name
    assert manifest.tier == "precision"
    assert manifest.containers  # if provides model_container

def test_containers_registered():
    from bioagent.model_zoo.registry import ModelRegistry
    ModelRegistry.discover()
    for name in manifest.containers:
        assert name in ModelRegistry.list_containers()
```

---

## 10. Publishing

### Name your package
```
bioagent-tier2-<short-name>
```

### PyPI
```bash
pip install build
python -m build
twine upload dist/*
```

### Submit to the BioAgent tier registry
Open a PR to [bioagent](https://github.com/your-org/bioagent) adding your package to the tier table in `README.md`:

```markdown
| Precision DNA‑LM | `bioagent-tier2-dna-lm` | DNA mutation effect prediction | stable |
```

### License
Academic/non‑profit tier packages: **CC BY‑NC 4.0**
Fully open: **MIT**

---

*Questions? Open an issue at [github.com/your-org/bioagent](https://github.com/your-org/bioagent).*