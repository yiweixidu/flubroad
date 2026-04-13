"""
flubroad/skill.py
SkillManifest — the contract between the FluBroad core framework and domain Skill packages.

Every Skill package declares one SkillManifest instance and registers it via
a pyproject.toml entry point so the framework can discover it at runtime.

Registration (in your Skill package's pyproject.toml):
-------------------------------------------------------
    [project.entry-points."flubroad.skills"]
    virology = "biovoice.skill:manifest"

Discovery (by the framework):
------------------------------
    from flubroad.core.skill_loader import SkillLoader
    skill = SkillLoader.load("virology")   # finds the installed Skill

Minimal Skill example:
-----------------------
    from flubroad.skill import SkillManifest

    manifest = SkillManifest(
        name    = "oncology",
        version = "0.1.0",
        display_name = "FluBroad Oncology Skill",
        agents  = ["pubmed", "europe_pmc", "tcga", "clinicaltrials"],
        section_queries = {
            "results":    "KRAS G12C NSCLC targeted therapy clinical outcome",
            "mechanisms": "RAS GTPase signalling pathway inhibitor resistance",
        },
        section_instructions = {
            "results": (
                "Summarise Phase II/III trial results for KRAS G12C inhibitors. "
                "Include ORR, PFS, OS. Cite every claim with [PMID]."
            ),
        },
        extraction_schema = {...},   # JSON schema for entity extraction
        topic_keywords    = ["kras", "nsclc", "sotorasib", "adagrasib"],
    )

See docs/skill-spec.md for the full specification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── SkillManifest ─────────────────────────────────────────────────────────────

@dataclass
class SkillManifest:
    """
    Declarative manifest for a FluBroad Skill package.

    A SkillManifest tells the FluBroad orchestrator everything it needs to
    run the pipeline for a given biomedical domain: which agents to use,
    how to query and synthesise each review section, what entities to extract,
    and which keywords define topic relevance.

    Required fields
    ---------------
    name                : str
        Short machine-readable identifier. Must be unique in the registry.
        Used in CLI: ``flubroad run --skill <name>``.
        Convention: lowercase, hyphens allowed (e.g. "virology", "oncology").

    version             : str
        Semantic version string (e.g. "1.0.0").

    display_name        : str
        Human-readable name shown in the UI and logs.

    agents              : List[str]
        Agent keys this Skill uses by default. Must be registered as
        ``flubroad.agents`` entry points (either by this Skill package
        or by the framework itself). Example: ["pubmed", "pdb", "iedb"].

    section_queries     : Dict[str, str]
        RAG retrieval queries, one per output section.
        Keys are section identifiers (e.g. "problem", "results").
        Values are keyword-dense search strings sent to the vector store.

    section_instructions : Dict[str, str]
        LLM prompts, one per output section.
        Each instruction must include citation requirements.
        Keys must match section_queries keys.

    extraction_schema   : Dict[str, Any]
        JSON schema for the primary entity type this Skill extracts
        (e.g. antibody, mutation, drug). Used by the orchestrator to
        call the LLM for structured extraction after synthesis.

    Optional fields
    ---------------
    description         : str
        One-paragraph description for documentation and the Skill registry.

    topic_keywords      : List[str]
        Domain keywords used to filter relevant corpus items (Jaccard scoring).
        More keywords = stricter relevance filter.

    default_agents      : List[str]
        Subset of ``agents`` used when the user does not specify --agents.
        Defaults to all agents in ``agents`` if not set.

    system_prompt       : str
        LLM system message prepended to every synthesis call.
        Should establish the expert persona appropriate for this domain.

    grant_templates     : Dict[str, str]
        Section keys and instructions for grant-writing mode.
        If empty, the orchestrator uses section_instructions for grant mode too.

    knowledge_graph_config : Dict[str, Any]
        Configuration for entity extraction patterns used by FluBroadGraph.
        Keys: "node_types", "edge_types", "entity_patterns" (regex strings).
        Leave empty to use the framework's default generic patterns.

    output_section_order : List[str]
        Ordered list of section keys for report assembly.
        Defaults to list(section_queries.keys()).

    output_section_titles : Dict[str, str]
        Display titles for each section key.
        Example: {"results": "Key Results & Broadly Neutralizing Antibodies"}

    finetuning_config   : Dict[str, Any]
        Hints for the fine-tuning loop (FeedbackStore + LoRA export).
        Keys: "base_model" (default HF model ID), "lora_rank" (int),
              "feedback_dir" (path), "min_examples_to_train" (int).

    chart_config        : Dict[str, Any]
        Hints for automatic chart generation in PPT.
        Keys: "strain_chart" (bool), "trend_chart" (bool),
              "heatmap_source_agent" (str).

    Notes
    -----
    - All Dict fields default to empty dicts; List fields to empty lists.
    - The orchestrator treats any missing optional field gracefully — it
      either falls back to a framework default or skips the feature.
    - Do not put secrets, file paths, or machine-specific config here.
      Use AgentConfig.extra_params (loaded from env/.env) for that.
    """

    # ── Required ──────────────────────────────────────────────────────────────
    name:                  str
    version:               str
    display_name:          str
    agents:                List[str]
    section_queries:       Dict[str, str]
    section_instructions:  Dict[str, str]
    extraction_schema:     Dict[str, Any]

    # ── Recommended ───────────────────────────────────────────────────────────
    description:           str         = ""
    topic_keywords:        List[str]   = field(default_factory=list)
    system_prompt:         str         = ""

    # ── Optional ──────────────────────────────────────────────────────────────
    default_agents:        List[str]   = field(default_factory=list)
    grant_templates:       Dict[str, str] = field(default_factory=dict)
    knowledge_graph_config: Dict[str, Any] = field(default_factory=dict)
    output_section_order:  List[str]   = field(default_factory=list)
    output_section_titles: Dict[str, str] = field(default_factory=dict)
    finetuning_config:     Dict[str, Any] = field(default_factory=dict)
    chart_config:          Dict[str, Any] = field(default_factory=dict)

    # ── Derived helpers ───────────────────────────────────────────────────────

    def __post_init__(self):
        if not self.default_agents:
            self.default_agents = list(self.agents)
        if not self.output_section_order:
            self.output_section_order = list(self.section_queries.keys())
        if not self.system_prompt:
            self.system_prompt = (
                f"You are an expert {self.display_name} research assistant. "
                "Write accurate, well-cited biomedical synthesis sections. "
                "Cite every factual claim with the PMID in parentheses."
            )

    @property
    def sections(self) -> List[str]:
        """Ordered list of section keys."""
        return self.output_section_order

    def section_title(self, key: str) -> str:
        """Return display title for a section key, falling back to title-cased key."""
        return self.output_section_titles.get(key, key.replace("_", " ").title())

    def is_relevant(self, title: str, abstract: str, min_hits: int = 1) -> bool:
        """
        Return True if a corpus item appears relevant to this Skill's domain.
        Uses topic_keywords for a simple bag-of-words check.
        """
        if not self.topic_keywords:
            return True
        text = (title + " " + abstract).lower()
        hits = sum(1 for kw in self.topic_keywords if kw.lower() in text)
        return hits >= min_hits

    def summary(self) -> str:
        """One-line description for logging."""
        return (
            f"Skill({self.name} v{self.version}) | "
            f"{len(self.agents)} agents | "
            f"{len(self.section_queries)} sections"
        )


# ── SkillLoader ───────────────────────────────────────────────────────────────

class SkillLoader:
    """
    Discovers and loads installed FluBroad Skill packages via entry points.

    Usage
    -----
        skill = SkillLoader.load("virology")
        print(skill.display_name)   # "BioVoice: Virology & bnAb Research"

        # List all installed Skills
        for name, skill in SkillLoader.all().items():
            print(name, skill.version)
    """

    _GROUP = "flubroad.skills"

    @classmethod
    def load(cls, name: str) -> SkillManifest:
        """
        Load a Skill by name.

        Parameters
        ----------
        name : the Skill's ``name`` field (e.g. "virology", "oncology")

        Raises
        ------
        SkillNotFoundError  if no installed package registers this Skill name
        TypeError           if the entry point does not resolve to a SkillManifest
        """
        skills = cls._discover()
        if name not in skills:
            available = ", ".join(sorted(skills)) or "none"
            raise SkillNotFoundError(
                f"Skill '{name}' not found. "
                f"Installed Skills: {available}. "
                f"Install one with: pip install flubroad-skill-{name}"
            )
        manifest = skills[name]
        if not isinstance(manifest, SkillManifest):
            raise TypeError(
                f"Entry point 'flubroad.skills:{name}' must resolve to a "
                f"SkillManifest instance, got {type(manifest).__name__}"
            )
        return manifest

    @classmethod
    def all(cls) -> Dict[str, SkillManifest]:
        """Return a dict of all installed Skills keyed by name."""
        return cls._discover()

    @classmethod
    def names(cls) -> List[str]:
        """Return sorted list of installed Skill names."""
        return sorted(cls._discover().keys())

    @classmethod
    def _discover(cls) -> Dict[str, SkillManifest]:
        """Load all entry points in the 'flubroad.skills' group."""
        import importlib.metadata as importlib_metadata
        skills: Dict[str, SkillManifest] = {}
        try:
            eps = importlib_metadata.entry_points(group=cls._GROUP)
        except Exception:
            return skills
        for ep in eps:
            try:
                manifest = ep.load()
                if isinstance(manifest, SkillManifest):
                    skills[manifest.name] = manifest
            except Exception as exc:
                import warnings
                warnings.warn(
                    f"Failed to load Skill from entry point '{ep.name}': {exc}",
                    stacklevel=2,
                )
        return skills


# ── Exceptions ────────────────────────────────────────────────────────────────

class SkillNotFoundError(Exception):
    """Raised when a requested Skill is not installed."""
