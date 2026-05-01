"""
Tests for the TierManifest dataclass and TierLoader.
No network calls, no external dependencies.
"""

import pytest
from bioagent.tier import TierManifest, TierLoader, TierNotFoundError


# ── Minimal valid manifest fixtures ────────────────────────────────────────

MODEL_CONTAINERS = {
    "dna-lm": "test_tier.containers.dna:DNAContainer",
    "ppi": "test_tier.containers.ppi:PPIContainer",
}

MODELS_METADATA = {
    "dna-lm": {
        "architecture": "DNABERT-2",
        "parameters": "110M",
        "min_vram_gb": 8,
    },
    "ppi": {
        "architecture": "SEHI-PPI",
        "parameters": "68M",
        "min_vram_gb": 6,
    },
}


@pytest.fixture
def minimal_precision_manifest():
    """A valid Tier 2 (Precision) manifest with two model containers."""
    return TierManifest(
        name="precision-pack",
        version="1.0.0",
        tier="precision",
        display_name="Precision Pack",
        provides=["model_container"],
        containers=MODEL_CONTAINERS,
        models=MODELS_METADATA,
    )


@pytest.fixture
def minimal_fusion_manifest():
    """A valid Tier 3 (Fusion) manifest with ETL adapters."""
    return TierManifest(
        name="fusion-pack",
        version="0.1.0",
        tier="fusion",
        display_name="Fusion Pack",
        provides=["etl_adapter"],
        etl_adapters={
            "fastq": "fusion_pack.etl:FastqLoader",
        },
        supported_formats={
            "fastq": ["fastq", "fastq.gz"],
        },
    )


@pytest.fixture
def minimal_horizontal_manifest():
    """A valid horizontal layer manifest."""
    return TierManifest(
        name="compliance-pack",
        version="0.2.0",
        tier="horizontal",
        display_name="Compliance Pack",
        provides=["compliance_template", "feedback_loop"],
        horizontals={
            "compliance": "comp_pack.compliance:Loi25Report",
        },
    )


# ── Required field tests ──────────────────────────────────────────────────

def test_manifest_type(minimal_precision_manifest):
    assert isinstance(minimal_precision_manifest, TierManifest)


def test_required_fields_precision(minimal_precision_manifest):
    m = minimal_precision_manifest
    assert m.name == "precision-pack"
    assert m.version == "1.0.0"
    assert m.tier == "precision"
    assert m.display_name == "Precision Pack"
    assert m.provides == ["model_container"]
    assert m.containers == MODEL_CONTAINERS
    assert m.models == MODELS_METADATA


def test_default_requires_gpu(minimal_precision_manifest):
    assert minimal_precision_manifest.requires_gpu is True


# ── Validation tests (__post_init__) ──────────────────────────────────────

def test_invalid_tier_raises():
    with pytest.raises(ValueError, match="tier must be one of"):
        TierManifest(
            name="bad",
            version="1.0.0",
            tier="nonexistent",
            display_name="Bad",
            provides=["model_container"],
            containers={"m": "p:Cls"},
            models={"m": {}},
        )


def test_invalid_provides_raises():
    with pytest.raises(ValueError, match="Invalid provides value"):
        TierManifest(
            name="bad",
            version="1.0.0",
            tier="precision",
            display_name="Bad",
            provides=["unknown_component"],
        )


def test_model_container_requires_containers_dict():
    with pytest.raises(ValueError, match="requires 'containers' dict"):
        TierManifest(
            name="bad",
            version="1.0.0",
            tier="precision",
            display_name="Bad",
            provides=["model_container"],
        )


def test_model_container_requires_models_dict():
    with pytest.raises(ValueError, match="requires 'models' dict"):
        TierManifest(
            name="bad",
            version="1.0.0",
            tier="precision",
            display_name="Bad",
            provides=["model_container"],
            containers={"m": "p:Cls"},
        )


def test_models_keys_must_match_containers():
    with pytest.raises(ValueError, match="keys.*not present in containers"):
        TierManifest(
            name="bad",
            version="1.0.0",
            tier="precision",
            display_name="Bad",
            provides=["model_container"],
            containers={"a": "p:Cls"},
            models={"b": {}},  # mismatched
        )


def test_containers_keys_missing_from_models():
    with pytest.raises(ValueError, match="lack entries in models"):
        TierManifest(
            name="bad",
            version="1.0.0",
            tier="precision",
            display_name="Bad",
            provides=["model_container"],
            containers={"a": "p:Cls", "b": "p:Cls2"},
            models={"a": {}},  # missing b
        )


def test_etl_adapter_requires_etl_adapters():
    with pytest.raises(ValueError, match="requires 'etl_adapters' dict"):
        TierManifest(
            name="bad",
            version="1.0.0",
            tier="fusion",
            display_name="Bad",
            provides=["etl_adapter"],
        )


# ── Default value tests ───────────────────────────────────────────────────

def test_empty_optional_fields(minimal_precision_manifest):
    m = minimal_precision_manifest
    assert m.description == ""
    assert m.hardware_requirements == {}
    assert m.docker_compose_fragment == ""
    assert m.horizontals == {}
    assert m.compliance_templates == {}
    assert m.finetuning_config == {}
    assert m.etl_adapters == {}
    assert m.supported_formats == {}


def test_requires_gpu_explicit_false():
    m = TierManifest(
        name="t",
        version="1.0.0",
        tier="precision",
        display_name="T",
        provides=["model_container"],
        containers={"a": "p:Cls"},
        models={"a": {}},
        requires_gpu=False,
    )
    assert m.requires_gpu is False


# ── Property and helper tests ─────────────────────────────────────────────

def test_sections_property(minimal_precision_manifest):
    """sections returns sorted provides list."""
    assert minimal_precision_manifest.sections == ["model_container"]


def test_sections_property_multiple(minimal_horizontal_manifest):
    assert minimal_horizontal_manifest.sections == sorted(["compliance_template", "feedback_loop"])


def test_container_metadata(minimal_precision_manifest):
    m = minimal_precision_manifest
    assert m.container_metadata("dna-lm")["architecture"] == "DNABERT-2"
    assert m.container_metadata("ppi")["parameters"] == "68M"
    assert m.container_metadata("nonexistent") == {}


def test_summary(minimal_precision_manifest):
    s = minimal_precision_manifest.summary()
    assert "precision-pack" in s
    assert "1.0.0" in s
    assert "precision" in s
    assert "model_container" in s
    assert "2" in s  # 2 containers


def test_summary_fusion(minimal_fusion_manifest):
    s = minimal_fusion_manifest.summary()
    assert "fusion-pack" in s
    assert "fusion" in s
    assert "etl_adapter" in s
    assert "1" in s  # 1 etl adapter


# ── TierLoader tests ─────────────────────────────────────────────────────

def test_tier_loader_unknown_raises():
    with pytest.raises(TierNotFoundError):
        TierLoader.load("definitely-not-a-real-tier-xyzzy")


def test_tier_loader_all_returns_dict():
    result = TierLoader.all()
    assert isinstance(result, dict)


def test_tier_loader_names_returns_list():
    names = TierLoader.names()
    assert isinstance(names, list)
    # In a test environment with no installed tier packages, names should be empty.
    # (or contain whatever is registered via entry points)
    assert "definitely-not-a-real-tier" not in names