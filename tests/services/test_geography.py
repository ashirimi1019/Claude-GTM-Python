"""Geography service tests."""

from services.geography import (
    DEFAULT_ALLOWED_COUNTRIES,
    build_apollo_location_filter,
    check_company_geography,
    filter_companies_by_geography,
    resolve_geography,
)


class TestDefaultCountries:
    def test_includes_us(self):
        assert "United States" in DEFAULT_ALLOWED_COUNTRIES

    def test_includes_canada(self):
        assert "Canada" in DEFAULT_ALLOWED_COUNTRIES

    def test_excludes_singapore(self):
        assert "Singapore" not in DEFAULT_ALLOWED_COUNTRIES

    def test_excludes_india(self):
        assert "India" not in DEFAULT_ALLOWED_COUNTRIES

    def test_excludes_uk(self):
        assert "United Kingdom" not in DEFAULT_ALLOWED_COUNTRIES


class TestResolveGeography:
    def test_defaults_to_americas(self):
        countries, states = resolve_geography()
        assert countries == DEFAULT_ALLOWED_COUNTRIES
        assert states is None

    def test_offer_overrides_default(self):
        countries, _ = resolve_geography(offer_countries=["United Kingdom"])
        assert countries == ["United Kingdom"]

    def test_campaign_overrides_offer(self):
        countries, _ = resolve_geography(
            offer_countries=["United States"],
            campaign_countries=["United Kingdom"],
        )
        assert countries == ["United Kingdom"]

    def test_states_resolved(self):
        _, states = resolve_geography(
            offer_states=["CA", "NY"],
            campaign_states=["TX"],
        )
        assert states == ["TX"]


class TestCheckCompanyGeography:
    def test_us_company_passes(self):
        assert check_company_geography(
            {"country": "United States"},
            DEFAULT_ALLOWED_COUNTRIES,
        ) is True

    def test_india_company_rejected(self):
        assert check_company_geography(
            {"country": "India"},
            DEFAULT_ALLOWED_COUNTRIES,
        ) is False

    def test_empty_country_rejected(self):
        assert check_company_geography(
            {"country": ""},
            DEFAULT_ALLOWED_COUNTRIES,
        ) is False

    def test_case_insensitive(self):
        assert check_company_geography(
            {"country": "united states"},
            DEFAULT_ALLOWED_COUNTRIES,
        ) is True

    def test_state_filter_passes(self):
        assert check_company_geography(
            {"country": "United States", "state": "CA"},
            ["United States"],
            ["CA", "NY"],
        ) is True

    def test_state_filter_rejects(self):
        assert check_company_geography(
            {"country": "United States", "state": "TX"},
            ["United States"],
            ["CA", "NY"],
        ) is False

    def test_countries_array_checked(self):
        assert check_company_geography(
            {"country": "", "countries": ["Canada"]},
            DEFAULT_ALLOWED_COUNTRIES,
        ) is True


class TestFilterCompaniesByGeography:
    def test_filters_correctly(self):
        companies = [
            {"name": "Acme US", "country": "United States"},
            {"name": "Acme IN", "country": "India"},
            {"name": "Acme CA", "country": "Canada"},
            {"name": "Acme SG", "country": "Singapore"},
        ]
        result = filter_companies_by_geography(companies, DEFAULT_ALLOWED_COUNTRIES)
        assert len(result) == 2
        assert result[0]["name"] == "Acme US"
        assert result[1]["name"] == "Acme CA"

    def test_empty_list(self):
        result = filter_companies_by_geography([], DEFAULT_ALLOWED_COUNTRIES)
        assert result == []


class TestBuildApolloLocationFilter:
    def test_countries_only(self):
        result = build_apollo_location_filter(["United States", "Canada"])
        assert result["organization_locations"] == ["United States", "Canada"]
        assert "person_locations" not in result

    def test_with_states(self):
        result = build_apollo_location_filter(["United States"], ["CA", "NY"])
        assert "person_locations" in result
        assert "United States, CA" in result["person_locations"]
