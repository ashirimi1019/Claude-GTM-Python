"""ICP Validator — validates raw ICP profile dicts before normalization.

Returns all errors (does not short-circuit) so the UI can display them all at once.
"""

from __future__ import annotations

from .constants import STRICTNESS_BUNDLES


def validate_icp_profile(profile: dict) -> dict:
    """Validate an ICP profile dict. Returns {"valid": bool, "errors": list[str]}."""
    errors: list[str] = []

    if not isinstance(profile, dict):
        return {"valid": False, "errors": ["profile must be a dict"]}

    # version
    version = profile.get("version")
    if version != 1:
        errors.append(f"version must be 1, got {version!r}")

    # mode
    mode = profile.get("mode")
    if mode not in ("basic", "advanced"):
        errors.append(f"mode must be 'basic' or 'advanced', got {mode!r}")

    # strictness
    strictness = profile.get("strictness")
    if strictness is not None:
        if not isinstance(strictness, dict):
            errors.append("strictness must be a dict")
        else:
            level = strictness.get("level")
            if level not in STRICTNESS_BUNDLES:
                valid_levels = ", ".join(sorted(STRICTNESS_BUNDLES.keys()))
                errors.append(f"strictness.level must be one of [{valid_levels}], got {level!r}")

    # hardFilters
    hard_filters = profile.get("hardFilters") or profile.get("hard_filters")
    if hard_filters is not None:
        if not isinstance(hard_filters, dict):
            errors.append("hardFilters must be a dict")
        else:
            _validate_hard_filters(hard_filters, errors)

    # scoring
    scoring = profile.get("scoring")
    if scoring is not None:
        if not isinstance(scoring, dict):
            errors.append("scoring must be a dict")
        else:
            _validate_scoring(scoring, errors)

    # enrichment
    enrichment = profile.get("enrichment")
    if enrichment is not None:
        if not isinstance(enrichment, dict):
            errors.append("enrichment must be a dict")
        else:
            _validate_enrichment(enrichment, errors)

    return {"valid": len(errors) == 0, "errors": errors}


def _validate_hard_filters(hf: dict, errors: list[str]) -> None:
    """Validate hardFilters section."""
    cs = hf.get("company_size") or hf.get("companySize")
    if cs is not None:
        if not isinstance(cs, dict):
            errors.append("hardFilters.company_size must be a dict")
        else:
            hard_min = cs.get("hardMin") or cs.get("hard_min")
            hard_max = cs.get("hardMax") or cs.get("hard_max")
            if hard_min is not None and hard_max is not None:
                if not isinstance(hard_min, (int, float)):
                    errors.append("hardFilters.company_size.hardMin must be a number")
                elif not isinstance(hard_max, (int, float)):
                    errors.append("hardFilters.company_size.hardMax must be a number")
                elif hard_min >= hard_max:
                    errors.append(
                        f"hardFilters.company_size: hardMin ({hard_min}) must be less than hardMax ({hard_max})"
                    )


def _validate_scoring(scoring: dict, errors: list[str]) -> None:
    """Validate scoring section."""
    cs = scoring.get("companySize") or scoring.get("company_size")
    if cs is not None and isinstance(cs, dict):
        ideal = cs.get("ideal")
        if ideal is not None:
            if not isinstance(ideal, list) or len(ideal) < 2:
                errors.append("scoring.companySize.ideal must be a list of [min, max]")
            elif ideal[0] > ideal[1]:
                errors.append(
                    f"scoring.companySize.ideal: ideal[0] ({ideal[0]}) must be <= ideal[1] ({ideal[1]})"
                )


def _validate_enrichment(enrichment: dict, errors: list[str]) -> None:
    """Validate enrichment section."""
    max_contacts = enrichment.get("maxContactsPerCompany", enrichment.get("max_contacts_per_company"))
    if max_contacts is not None:
        if not isinstance(max_contacts, (int, float)):
            errors.append("enrichment.maxContactsPerCompany must be a number")
        elif max_contacts < 1 or max_contacts > 25:
            errors.append(
                f"enrichment.maxContactsPerCompany must be between 1 and 25, got {max_contacts}"
            )
