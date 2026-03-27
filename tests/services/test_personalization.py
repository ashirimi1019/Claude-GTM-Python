"""Personalization service tests."""

from services.personalization import (
    build_signal_reference,
    personalize_email_body,
    personalize_linkedin_message,
)


class TestPersonalizeEmailBody:
    def test_replaces_all_tokens(self):
        template = "Hi {firstName}, I noticed {companyName} in {industry}."
        result = personalize_email_body(
            template,
            contact={"first_name": "John", "last_name": "Doe"},
            company={"name": "Acme Corp", "industry": "Technology"},
        )
        assert result == "Hi John, I noticed Acme Corp in Technology."

    def test_missing_fields_become_empty(self):
        template = "Hi {firstName} at {companyName}"
        result = personalize_email_body(
            template,
            contact={},
            company={},
        )
        assert result == "Hi  at "

    def test_campaign_name_token(self):
        template = "Re: {campaignName}"
        result = personalize_email_body(
            template,
            contact={},
            company={},
            campaign={"title": "Q1 Outreach"},
        )
        assert result == "Re: Q1 Outreach"


class TestPersonalizeLinkedInMessage:
    def test_replaces_tokens(self):
        template = "Hi {firstName}, love what {companyName} is doing."
        result = personalize_linkedin_message(
            template,
            contact={"first_name": "Jane"},
            company={"name": "Beta Inc"},
        )
        assert result == "Hi Jane, love what Beta Inc is doing."


class TestBuildSignalReference:
    def test_job_posting(self):
        result = build_signal_reference({
            "signal_type": "job_posting",
            "signal_name": "Python Developer",
        })
        assert "Python Developer" in result
        assert "posted" in result

    def test_recent_funding_with_amount(self):
        result = build_signal_reference({
            "signal_type": "recent_funding",
            "signal_name": "Series A",
            "details": {"amount": 5000000},
        })
        assert "$5,000,000" in result

    def test_recent_funding_without_amount(self):
        result = build_signal_reference({
            "signal_type": "recent_funding",
            "signal_name": "Series A",
        })
        assert "funding round" in result

    def test_growth_metrics(self):
        result = build_signal_reference({
            "signal_type": "growth_metrics",
            "signal_name": "headcount",
        })
        assert "headcount" in result

    def test_bombora_intent(self):
        result = build_signal_reference({
            "signal_type": "bombora_intent",
            "signal_name": "cloud migration",
        })
        assert "cloud migration" in result

    def test_unknown_type(self):
        result = build_signal_reference({
            "signal_type": "other",
            "signal_name": "something",
        })
        assert "something" in result
