"""Tests for services.icp.validator."""


from services.icp.validator import validate_icp_profile

# --- Valid profiles ---

def test_minimal_valid_profile():
    result = validate_icp_profile({"version": 1, "mode": "basic"})
    assert result["valid"] is True
    assert result["errors"] == []


def test_full_valid_profile():
    profile = {
        "version": 1,
        "mode": "advanced",
        "strictness": {"level": "balanced"},
        "hardFilters": {
            "company_size": {"hardMin": 50, "hardMax": 500},
        },
        "scoring": {
            "companySize": {"ideal": [100, 400]},
        },
        "enrichment": {
            "maxContactsPerCompany": 5,
        },
    }
    result = validate_icp_profile(profile)
    assert result["valid"] is True
    assert result["errors"] == []


# --- Version errors ---

def test_missing_version():
    result = validate_icp_profile({"mode": "basic"})
    assert result["valid"] is False
    assert any("version must be 1" in e for e in result["errors"])


def test_wrong_version():
    result = validate_icp_profile({"version": 2, "mode": "basic"})
    assert result["valid"] is False
    assert any("version must be 1" in e for e in result["errors"])


# --- Mode errors ---

def test_missing_mode():
    result = validate_icp_profile({"version": 1})
    assert result["valid"] is False
    assert any("mode must be" in e for e in result["errors"])


def test_invalid_mode():
    result = validate_icp_profile({"version": 1, "mode": "expert"})
    assert result["valid"] is False
    assert any("mode must be" in e for e in result["errors"])


# --- Strictness errors ---

def test_invalid_strictness_level():
    profile = {
        "version": 1,
        "mode": "basic",
        "strictness": {"level": "ultra"},
    }
    result = validate_icp_profile(profile)
    assert result["valid"] is False
    assert any("strictness.level" in e for e in result["errors"])


def test_valid_strictness_levels():
    for level in ("broad", "balanced", "strict", "very_strict"):
        profile = {"version": 1, "mode": "basic", "strictness": {"level": level}}
        result = validate_icp_profile(profile)
        assert result["valid"] is True, f"level '{level}' should be valid"


# --- Hard filter company_size errors ---

def test_hard_min_greater_than_hard_max():
    profile = {
        "version": 1,
        "mode": "basic",
        "hardFilters": {
            "company_size": {"hardMin": 500, "hardMax": 100},
        },
    }
    result = validate_icp_profile(profile)
    assert result["valid"] is False
    assert any("hardMin" in e and "hardMax" in e for e in result["errors"])


def test_hard_min_equals_hard_max():
    profile = {
        "version": 1,
        "mode": "basic",
        "hardFilters": {
            "company_size": {"hardMin": 100, "hardMax": 100},
        },
    }
    result = validate_icp_profile(profile)
    assert result["valid"] is False
    assert any("hardMin" in e for e in result["errors"])


def test_hard_min_less_than_hard_max_valid():
    profile = {
        "version": 1,
        "mode": "basic",
        "hardFilters": {
            "company_size": {"hardMin": 50, "hardMax": 500},
        },
    }
    result = validate_icp_profile(profile)
    assert result["valid"] is True


# --- Scoring companySize ideal bands ---

def test_scoring_ideal_band_invalid():
    profile = {
        "version": 1,
        "mode": "basic",
        "scoring": {
            "companySize": {"ideal": [500, 100]},
        },
    }
    result = validate_icp_profile(profile)
    assert result["valid"] is False
    assert any("ideal[0]" in e for e in result["errors"])


def test_scoring_ideal_band_valid():
    profile = {
        "version": 1,
        "mode": "basic",
        "scoring": {
            "companySize": {"ideal": [100, 500]},
        },
    }
    result = validate_icp_profile(profile)
    assert result["valid"] is True


def test_scoring_ideal_band_equal_valid():
    profile = {
        "version": 1,
        "mode": "basic",
        "scoring": {
            "companySize": {"ideal": [200, 200]},
        },
    }
    result = validate_icp_profile(profile)
    assert result["valid"] is True


# --- Enrichment maxContactsPerCompany ---

def test_enrichment_max_contacts_too_low():
    profile = {
        "version": 1,
        "mode": "basic",
        "enrichment": {"maxContactsPerCompany": 0},
    }
    result = validate_icp_profile(profile)
    assert result["valid"] is False
    assert any("between 1 and 25" in e for e in result["errors"])


def test_enrichment_max_contacts_too_high():
    profile = {
        "version": 1,
        "mode": "basic",
        "enrichment": {"maxContactsPerCompany": 50},
    }
    result = validate_icp_profile(profile)
    assert result["valid"] is False
    assert any("between 1 and 25" in e for e in result["errors"])


def test_enrichment_max_contacts_valid_boundary():
    for val in (1, 25):
        profile = {
            "version": 1,
            "mode": "basic",
            "enrichment": {"maxContactsPerCompany": val},
        }
        result = validate_icp_profile(profile)
        assert result["valid"] is True, f"maxContactsPerCompany={val} should be valid"


# --- Multiple errors collected ---

def test_multiple_errors_not_short_circuited():
    profile = {
        "version": 2,
        "mode": "expert",
        "strictness": {"level": "ultra"},
        "hardFilters": {
            "company_size": {"hardMin": 500, "hardMax": 100},
        },
        "enrichment": {"maxContactsPerCompany": 0},
    }
    result = validate_icp_profile(profile)
    assert result["valid"] is False
    assert len(result["errors"]) >= 4  # version, mode, strictness, company_size, enrichment


# --- Edge case: non-dict input ---

def test_non_dict_profile():
    result = validate_icp_profile("not a dict")  # type: ignore[arg-type]
    assert result["valid"] is False
    assert any("must be a dict" in e for e in result["errors"])
