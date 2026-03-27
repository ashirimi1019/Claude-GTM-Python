"""Pydantic model validation tests."""

import pytest

from models.campaign import CampaignCreate
from models.company import Company
from models.contact import Contact
from models.evidence import Evidence
from models.message import Message
from models.metrics import SequenceMetrics
from models.offer import OfferCreate, slugify


class TestSlugify:
    def test_basic_slugify(self):
        assert slugify("Talent as Service US") == "talent-as-service-us"

    def test_special_characters(self):
        assert slugify("AI & Data Consulting!") == "ai-data-consulting"

    def test_multiple_spaces(self):
        assert slugify("cloud   software   delivery") == "cloud-software-delivery"

    def test_leading_trailing_dashes(self):
        assert slugify("  --hello--  ") == "hello"


class TestOfferCreate:
    def test_auto_generates_slug(self):
        config = OfferCreate(name="Talent as Service US")
        assert config.slug == "talent-as-service-us"

    def test_preserves_explicit_slug(self):
        config = OfferCreate(name="Whatever", slug="my-custom-slug")
        assert config.slug == "my-custom-slug"


class TestCampaignCreate:
    def test_auto_generates_slug(self):
        config = CampaignCreate(offer_slug="test", name="Hiring Data Engineers")
        assert config.slug == "hiring-data-engineers"


class TestCompany:
    def test_optional_fields_default_none(self):
        company = Company(name="Acme", domain="acme.com")
        assert company.employee_count is None
        assert company.icp_tier is None
        assert company.tech_stack is None

    def test_all_fields_populated(self):
        company = Company(
            id="1", name="Acme", domain="acme.com",
            employee_count=500, icp_score=180.0, icp_tier="A",
        )
        assert company.employee_count == 500
        assert company.icp_tier == "A"


class TestContact:
    def test_email_required(self):
        with pytest.raises(Exception):
            Contact(id="1", first_name="John", last_name="Doe")  # missing email

    def test_email_provided(self):
        contact = Contact(email="john@acme.com", first_name="John", last_name="Doe")
        assert contact.email == "john@acme.com"
        assert contact.email_status == "unverified"


class TestMessage:
    def test_defaults(self):
        msg = Message(campaign_id="c1", contact_id="ct1", company_id="co1")
        assert msg.status == "draft"
        assert msg.channel == "email"


class TestEvidence:
    def test_defaults(self):
        ev = Evidence(company_id="c1", signal_name="Python Developer")
        assert ev.signal_type == "other"
        assert ev.source == "apollo"


class TestSequenceMetrics:
    def test_rates_with_data(self):
        m = SequenceMetrics(sent=100, opened=50, replied=10, bounced=3)
        assert m.open_rate == 0.5
        assert m.reply_rate == 0.1
        assert m.bounce_rate == 0.03

    def test_rates_with_zero_sent(self):
        m = SequenceMetrics()
        assert m.open_rate == 0.0
        assert m.reply_rate == 0.0
