"""Apollo client tests — using httpx mocking."""

import pytest

from clients.apollo.utils import normalize_domain
from clients.apollo.errors import handle_apollo_error, ApolloError
from clients.apollo.types import ApolloQueryParams
from clients.apollo.enrichment import merge_enriched_data
from clients.apollo.types import ApolloOrgEnrichmentResult


class TestNormalizeDomain:
    def test_basic_domain(self):
        assert normalize_domain("acme.com") == "acme.com"

    def test_uppercase(self):
        assert normalize_domain("ACME.COM") == "acme.com"

    def test_strip_protocol(self):
        assert normalize_domain("https://acme.com") == "acme.com"

    def test_strip_www(self):
        assert normalize_domain("www.acme.com") == "acme.com"

    def test_strip_path(self):
        assert normalize_domain("https://www.acme.com/about") == "acme.com"

    def test_strip_all(self):
        assert normalize_domain("  HTTPS://WWW.Acme.COM/page  ") == "acme.com"


class TestHandleApolloError:
    def test_rate_limited(self):
        err = handle_apollo_error(429)
        assert isinstance(err, ApolloError)
        assert err.retryable is True
        assert "rate limit" in err.message.lower()

    def test_auth_failed(self):
        err = handle_apollo_error(401)
        assert err.retryable is False
        assert err.apollo_code == "AUTH_FAILED"

    def test_insufficient_credits(self):
        err = handle_apollo_error(402)
        assert err.retryable is False
        assert "credits" in err.message.lower()

    def test_forbidden(self):
        err = handle_apollo_error(403)
        assert err.retryable is False

    def test_not_found(self):
        err = handle_apollo_error(404, "org not found")
        assert "not found" in err.message.lower()

    def test_validation_error(self):
        err = handle_apollo_error(422, "invalid param")
        assert err.apollo_code == "VALIDATION_ERROR"

    def test_server_error_retryable(self):
        err = handle_apollo_error(500)
        assert err.retryable is True

    def test_unknown_error(self):
        err = handle_apollo_error(418, "teapot")
        assert err.apollo_code == "UNKNOWN"


class TestMergeEnrichedData:
    def test_fills_missing_fields(self):
        sparse = {"name": "Acme", "industry": None, "employee_count": None}
        enriched = ApolloOrgEnrichmentResult(
            id="1", name="Acme", domain="acme.com",
            industry="Technology", employee_count=500,
        )
        result = merge_enriched_data(sparse, enriched)
        assert result["industry"] == "Technology"
        assert result["employee_count"] == 500

    def test_preserves_existing_values(self):
        sparse = {"name": "Acme", "industry": "Finance", "employee_count": 100}
        enriched = ApolloOrgEnrichmentResult(
            id="1", name="Acme", domain="acme.com",
            industry="Technology", employee_count=500,
        )
        result = merge_enriched_data(sparse, enriched)
        assert result["industry"] == "Finance"  # preserved
        assert result["employee_count"] == 100  # preserved

    def test_merges_tech_stack(self):
        sparse = {"name": "Acme", "tech_stack": ["Python"]}
        enriched = ApolloOrgEnrichmentResult(
            id="1", name="Acme", domain="acme.com",
            technology_names=["React", "Python"],  # Python already exists
        )
        result = merge_enriched_data(sparse, enriched)
        assert "Python" in result["tech_stack"]
        assert "React" in result["tech_stack"]
        # No duplicate Python
        assert result["tech_stack"].count("Python") == 1

    def test_case_insensitive_dedup(self):
        sparse = {"name": "Acme", "tech_stack": ["python"]}
        enriched = ApolloOrgEnrichmentResult(
            id="1", name="Acme", domain="acme.com",
            technology_names=["Python"],
        )
        result = merge_enriched_data(sparse, enriched)
        assert len(result["tech_stack"]) == 1  # no case-different duplicate

    def test_does_not_mutate_original(self):
        sparse = {"name": "Acme", "industry": None}
        enriched = ApolloOrgEnrichmentResult(
            id="1", name="Acme", domain="acme.com",
            industry="Tech",
        )
        merge_enriched_data(sparse, enriched)
        assert sparse["industry"] is None  # original unchanged


class TestApolloQueryParams:
    def test_defaults(self):
        params = ApolloQueryParams()
        assert params.per_page == 100
        assert params.page == 1

    def test_custom(self):
        params = ApolloQueryParams(
            employee_ranges=["1,10", "11,20"],
            keywords=["python", "react"],
        )
        assert len(params.employee_ranges) == 2
        assert len(params.keywords) == 2
