"""
Tests for the SkillManifest dataclass and SkillLoader.
No network calls, no external dependencies.
"""

import pytest
from flubroad.skill import SkillManifest, SkillLoader


# ── Minimal valid manifest fixture ──────────────────────────────────────────

SECTION_QUERIES = {
    "problem": "disease mutation incidence mortality",
    "results": "drug trial ORR PFS response",
}

SECTION_INSTRUCTIONS = {
    "problem": "Write the Problem section. Cite every claim with PMID. 150 words.",
    "results": "Write the Results section. Compare 3+ drugs. Cite PMID. 300 words.",
}

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "drug_name": {"type": "string"},
                    "target": {"type": "string"},
                    "key_pmids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["drug_name", "target"],
            },
        }
    },
}


@pytest.fixture
def minimal_manifest():
    return SkillManifest(
        name="test-skill",
        version="0.1.0",
        display_name="Test Skill",
        agents=["pubmed", "europe_pmc"],
        section_queries=SECTION_QUERIES,
        section_instructions=SECTION_INSTRUCTIONS,
        extraction_schema=EXTRACTION_SCHEMA,
    )


# ── Required field tests ─────────────────────────────────────────────────────

def test_manifest_type(minimal_manifest):
    assert isinstance(minimal_manifest, SkillManifest)


def test_required_fields(minimal_manifest):
    assert minimal_manifest.name == "test-skill"
    assert minimal_manifest.version == "0.1.0"
    assert minimal_manifest.display_name == "Test Skill"
    assert minimal_manifest.agents == ["pubmed", "europe_pmc"]
    assert minimal_manifest.section_queries
    assert minimal_manifest.section_instructions
    assert minimal_manifest.extraction_schema


def test_sections_consistent(minimal_manifest):
    assert set(minimal_manifest.section_queries.keys()) == set(
        minimal_manifest.section_instructions.keys()
    )


# ── Default value tests ──────────────────────────────────────────────────────

def test_default_agents_fallback(minimal_manifest):
    """When default_agents is not set, it defaults to the full agents list."""
    assert minimal_manifest.default_agents == ["pubmed", "europe_pmc"]


def test_output_section_order_fallback(minimal_manifest):
    """When output_section_order is not set, it matches section_queries keys."""
    assert set(minimal_manifest.output_section_order) == set(
        minimal_manifest.section_queries.keys()
    )


def test_system_prompt_auto_generated(minimal_manifest):
    """system_prompt is auto-generated from display_name when not provided."""
    assert "Test Skill" in minimal_manifest.system_prompt
    assert len(minimal_manifest.system_prompt) > 0


def test_empty_optional_fields(minimal_manifest):
    assert minimal_manifest.description == ""
    assert minimal_manifest.topic_keywords == []
    assert minimal_manifest.grant_templates == {}
    assert minimal_manifest.knowledge_graph_config == {}
    assert minimal_manifest.finetuning_config == {}
    assert minimal_manifest.chart_config == {}


# ── Property tests ───────────────────────────────────────────────────────────

def test_sections_property(minimal_manifest):
    assert minimal_manifest.sections == minimal_manifest.output_section_order


def test_section_title_custom():
    m = SkillManifest(
        name="t",
        version="1.0.0",
        display_name="T",
        agents=["pubmed"],
        section_queries={"results": "q"},
        section_instructions={"results": "i"},
        extraction_schema={},
        output_section_titles={"results": "Key Clinical Results"},
    )
    assert m.section_title("results") == "Key Clinical Results"


def test_section_title_fallback(minimal_manifest):
    """Titles not in output_section_titles fall back to title-cased key."""
    assert minimal_manifest.section_title("problem") == "Problem"


def test_summary(minimal_manifest):
    s = minimal_manifest.summary()
    assert "test-skill" in s
    assert "0.1.0" in s
    assert "2 agents" in s
    assert "2 sections" in s


# ── is_relevant tests ────────────────────────────────────────────────────────

def test_is_relevant_no_keywords(minimal_manifest):
    """No topic_keywords means everything is relevant."""
    assert minimal_manifest.is_relevant("anything", "at all") is True


def test_is_relevant_keyword_match():
    m = SkillManifest(
        name="t",
        version="1.0.0",
        display_name="T",
        agents=["pubmed"],
        section_queries={"r": "q"},
        section_instructions={"r": "i"},
        extraction_schema={},
        topic_keywords=["kras", "nsclc", "lung cancer"],
    )
    assert m.is_relevant("KRAS G12C mutation in NSCLC", "") is True
    assert m.is_relevant("unrelated title", "unrelated abstract") is False


def test_is_relevant_min_hits():
    m = SkillManifest(
        name="t",
        version="1.0.0",
        display_name="T",
        agents=["pubmed"],
        section_queries={"r": "q"},
        section_instructions={"r": "i"},
        extraction_schema={},
        topic_keywords=["kras", "nsclc"],
    )
    # Only 1 keyword hit, min_hits=2 should fail
    assert m.is_relevant("KRAS mutation in something", "", min_hits=2) is False
    # Both keywords present
    assert m.is_relevant("KRAS NSCLC study", "", min_hits=2) is True


# ── SkillLoader tests ────────────────────────────────────────────────────────

def test_skill_loader_unknown_raises():
    from flubroad.skill import SkillNotFoundError
    with pytest.raises(SkillNotFoundError):
        SkillLoader.load("definitely-not-a-real-skill-xyzzy")


def test_skill_loader_all_returns_dict():
    result = SkillLoader.all()
    assert isinstance(result, dict)
