"""
bioagent/agent/tier.py
TierManifest — the contract between the BioAgent core framework and tier packages.

Every tier package (Foundation, Precision, Fusion, Strategy) declares one
TierManifest instance and registers it via a pyproject.toml entry point so the
framework can discover it at runtime.

Registration (in your tier package's pyproject.toml):
-------------------------------------------------------
    [project.entry-points."bioagent.tiers"]
    precision = "tier2_precision.manifest:manifest"

Discovery (by the framework):
------------------------------
    from bioagent.core.tier_loader import TierLoader
    tier = TierLoader.load("precision")

Minimal tier example (Precision package with two model containers):
--------------------------------------------------------------------
    from bioagent.core.tier import TierManifest

    manifest = TierManifest(
        name         = "precision-pack",
        version      = "1.0.0",
        tier         = "precision",
        display_name = "Tier 2: Precision Molecular Intelligence",
        provides     = ["model_container"],
        containers   = {
            "dna-language-model": "tier2_precision.containers.dna_lm:DNALanguageModelContainer",
            "ppi-predictor":      "tier2_precision.containers.ppi:PPIPredictorContainer",
        },
        models       = {
            "dna-language-model": {
                "architecture": "DNABERT-2",
                "parameters":   "110M",
                "min_vram_gb":  8,
            },
            "ppi-predictor": {
                "architecture": "SEHI-PPI",
                "parameters":   "68M",
                "min_vram_gb":  6,
            },
        },
        requires_gpu = True,
        hardware_requirements = {
            "gpu":  "NVIDIA L40S",
            "vram": "24 GB",
            "ram":  "64 GB",
        },
    )

See docs/tier-spec.md for the full specification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── TierManifest ──────────────────────────────────────────────────────────────

@dataclass
class TierManifest:
    """
    Declarative manifest for a BioAgent tier package.

    A TierManifest tells the BioAgent orchestrator everything it needs to
    integrate a tier package: which component types it provides, which
    model containers or ETL adapters to load, what hardware is required,
    and how to deploy them.

    Required fields
    ---------------
    name                : str
        Short machine-readable identifier. Must be unique across all installed
        tier packages. Used in CLI: ``bioagent run --tier <name>``.
        Convention: lowercase, hyphens allowed (e.g. "precision-pack").

    version             : str
        Semantic version string (e.g. "1.0.0").

    tier                : str
        The commercial tier this package belongs to. Must be one of:
        ``"foundation"``, ``"precision"``, ``"fusion"``, ``"strategy"``,
        or ``"horizontal"``.

    display_name        : str
        Human-readable name shown in the UI and logs.

    provides            : List[str]
        Component types delivered by this package. Allowed values:
        ``"model_container"``, ``"etl_adapter"``, ``"compliance_template"``,
        ``"grant_template"``, ``"hypothesis_engine"``, ``"feedback_loop"``.
        Determines which additional fields become active.

    Model container fields (required if ``"model_container"`` in provides)
    -----------------------------------------------------------------------
    containers          : Dict[str, str]
        Mapping of container short name to fully qualified Python class path.
        Example: ``{"dna-language-model": "tier2_pack.containers.dna:DNAContainer"}``

    models              : Dict[str, Dict[str, Any]]
        Metadata for each container, must use the same keys as ``containers``.
        Each dict should include ``"architecture"``, ``"parameters"``,
        ``"min_vram_gb"``.

    requires_gpu        : bool
        Whether the containers need a GPU. Default ``True``.

    ETL adapter fields (required if ``"etl_adapter"`` in provides)
    ---------------------------------------------------------------
    etl_adapters        : Dict[str, str]
        Mapping of adapter name to class path.

    supported_formats   : Dict[str, List[str]]
        File formats each adapter can ingest.

    Optional fields
    ---------------
    description         : str
        One-paragraph description for documentation and the tier registry.

    hardware_requirements : Dict[str, Any]
        Minimal hardware needed to run this tier package.
        Example: ``{"gpu": "A10", "vram": "24 GB", "ram": "64 GB"}``.

    docker_compose_fragment : str
        Path to a Docker Compose YAML snippet that adds this package’s services.

    horizontals         : Dict[str, Any]
        Horizontal components provided by this package (hypothesis engines,
        feedback loop managers, compliance templates). Keys are component
        type names, values are class paths.

    compliance_templates : Dict[str, str]
        Mapping from template name to callable (used when ``"compliance_template"``
        is in ``provides``).

    finetuning_config   : Dict[str, Any]
        Hints for the model fine‑tuning loop (if this package provides base models).

    Notes
    -----
    - All Dict fields default to empty dicts; List fields to empty lists.
    - The orchestrator treats missing optional fields gracefully.
    - Do not put secrets, file paths, or machine‑specific config here.
      Use environment variables for that.
    """

    # ── Required ──────────────────────────────────────────────────────────────
    name:            str
    version:         str
    tier:            str               # "foundation", "precision", "fusion", "strategy", "horizontal"
    display_name:    str
    provides:        List[str]

    # ── Model container specific (required if provides contains "model_container") ──
    containers:      Dict[str, str]               = field(default_factory=dict)
    models:          Dict[str, Dict[str, Any]]    = field(default_factory=dict)
    requires_gpu:    bool                         = True

    # ── ETL adapter specific ──────────────────────────────────────────────────
    etl_adapters:    Dict[str, str]               = field(default_factory=dict)
    supported_formats: Dict[str, List[str]]       = field(default_factory=dict)

    # ── Recommended ───────────────────────────────────────────────────────────
    description:     str                          = ""
    hardware_requirements: Dict[str, Any]         = field(default_factory=dict)

    # ── Optional ──────────────────────────────────────────────────────────────
    docker_compose_fragment: str                  = ""
    horizontals:     Dict[str, Any]               = field(default_factory=dict)
    compliance_templates: Dict[str, str]          = field(default_factory=dict)
    finetuning_config: Dict[str, Any]             = field(default_factory=dict)

    # ── Derived helpers ───────────────────────────────────────────────────────

    def __post_init__(self):
        # Validate tier value
        valid_tiers = {"foundation", "precision", "fusion", "strategy", "horizontal"}
        if self.tier not in valid_tiers:
            raise ValueError(f"tier must be one of {valid_tiers}, got '{self.tier}'")

        # Validate provides values
        valid_provides = {
            "model_container", "etl_adapter", "compliance_template",
            "grant_template", "hypothesis_engine", "feedback_loop",
        }
        for p in self.provides:
            if p not in valid_provides:
                raise ValueError(f"Invalid provides value '{p}'. Allowed: {valid_provides}")

        # If model containers are provided, ensure containers and models are present
        if "model_container" in self.provides:
            if not self.containers:
                raise ValueError("'model_container' in provides requires 'containers' dict")
            if not self.models:
                raise ValueError("'model_container' in provides requires 'models' dict")
            # Ensure models keys match container keys
            extra = set(self.models.keys()) - set(self.containers.keys())
            if extra:
                raise ValueError(f"models keys {extra} not present in containers")
            missing = set(self.containers.keys()) - set(self.models.keys())
            if missing:
                raise ValueError(f"containers keys {missing} lack entries in models")

        # ETL adapters check
        if "etl_adapter" in self.provides and not self.etl_adapters:
            raise ValueError("'etl_adapter' in provides requires 'etl_adapters' dict")

    @property
    def sections(self) -> List[str]:
        """Return ordered list of tier component names (for logging)."""
        # This is a placeholder; tiers don't have sections like Skills.
        return sorted(self.provides)

    def container_metadata(self, name: str) -> Dict[str, Any]:
        """Return metadata dict for a registered container, or empty dict."""
        return self.models.get(name, {})

    def summary(self) -> str:
        """One-line description for logging."""
        return (
            f"Tier({self.name} v{self.version}, {self.tier}) | "
            f"provides: {', '.join(self.provides)} | "
            f"containers: {len(self.containers)}"
        )


# ── TierLoader ───────────────────────────────────────────────────────────────

class TierLoader:
    """
    Discovers and loads installed BioAgent tier packages via entry points.

    Usage
    -----
        tier = TierLoader.load("precision-pack")
        print(tier.display_name)   # "Tier 2: Precision Molecular Intelligence"

        # List all installed tier packages
        for name, tier in TierLoader.all().items():
            print(name, tier.version)
    """

    _GROUP = "bioagent.tiers"

    @classmethod
    def load(cls, name: str) -> TierManifest:
        """
        Load a tier package by name.

        Parameters
        ----------
        name : the tier's ``name`` field (e.g. "precision-pack")

        Raises
        ------
        TierNotFoundError  if no installed package registers this tier name
        TypeError          if the entry point does not resolve to a TierManifest
        """
        tiers = cls._discover()
        if name not in tiers:
            available = ", ".join(sorted(tiers)) or "none"
            raise TierNotFoundError(
                f"Tier '{name}' not found. "
                f"Installed tiers: {available}. "
                f"Install one with: pip install bioagent-tier-{name}"
            )
        manifest = tiers[name]
        if not isinstance(manifest, TierManifest):
            raise TypeError(
                f"Entry point 'bioagent.tiers:{name}' must resolve to a "
                f"TierManifest instance, got {type(manifest).__name__}"
            )
        return manifest

    @classmethod
    def all(cls) -> Dict[str, TierManifest]:
        """Return a dict of all installed tier packages keyed by name."""
        return cls._discover()

    @classmethod
    def names(cls) -> List[str]:
        """Return sorted list of installed tier names."""
        return sorted(cls._discover().keys())

    @classmethod
    def _discover(cls) -> Dict[str, TierManifest]:
        """Load all entry points in the 'bioagent.tiers' group."""
        import importlib.metadata as importlib_metadata
        tiers: Dict[str, TierManifest] = {}
        try:
            eps = importlib_metadata.entry_points(group=cls._GROUP)
        except Exception:
            return tiers
        for ep in eps:
            try:
                manifest = ep.load()
                if isinstance(manifest, TierManifest):
                    tiers[manifest.name] = manifest
            except Exception as exc:
                import warnings
                warnings.warn(
                    f"Failed to load Tier from entry point '{ep.name}': {exc}",
                    stacklevel=2,
                )
        return tiers


# ── Exceptions ────────────────────────────────────────────────────────────────

class TierNotFoundError(Exception):
    """Raised when a requested tier package is not installed."""