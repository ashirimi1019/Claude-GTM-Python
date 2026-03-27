"""Deduplication service tests."""

from services.deduplication import (
    deduplicate_companies,
    deduplicate_contacts,
    deduplicate_messages,
)


class TestDeduplicateContacts:
    def test_removes_duplicate_emails(self):
        contacts = [
            {"email": "john@acme.com", "first_name": "John"},
            {"email": "john@acme.com", "first_name": "John"},
        ]
        result = deduplicate_contacts(contacts)
        assert len(result) == 1

    def test_case_insensitive_email(self):
        contacts = [
            {"email": "John@Acme.com", "first_name": "John"},
            {"email": "john@acme.com", "first_name": "John"},
        ]
        result = deduplicate_contacts(contacts)
        assert len(result) == 1

    def test_merges_fields(self):
        contacts = [
            {"email": "john@acme.com", "first_name": "John", "title": None},
            {"email": "john@acme.com", "first_name": "John", "title": "CTO"},
        ]
        result = deduplicate_contacts(contacts)
        assert len(result) == 1
        assert result[0]["title"] == "CTO"

    def test_skips_empty_email(self):
        contacts = [
            {"email": "", "first_name": "Nobody"},
            {"email": "john@acme.com", "first_name": "John"},
        ]
        result = deduplicate_contacts(contacts)
        assert len(result) == 1
        assert result[0]["email"] == "john@acme.com"

    def test_preserves_unique(self):
        contacts = [
            {"email": "john@acme.com"},
            {"email": "jane@acme.com"},
        ]
        result = deduplicate_contacts(contacts)
        assert len(result) == 2


class TestDeduplicateCompanies:
    def test_removes_by_apollo_id(self):
        companies = [
            {"apollo_id": "a1", "name": "Acme", "domain": "acme.com"},
            {"apollo_id": "a1", "name": "Acme Inc", "domain": "acme.com"},
        ]
        result = deduplicate_companies(companies)
        assert len(result) == 1

    def test_removes_by_domain(self):
        companies = [
            {"apollo_id": "", "name": "Acme", "domain": "acme.com"},
            {"apollo_id": "", "name": "Acme Inc", "domain": "acme.com"},
        ]
        result = deduplicate_companies(companies)
        assert len(result) == 1

    def test_merges_arrays(self):
        companies = [
            {"apollo_id": "a1", "domain": "acme.com", "tech_stack": ["Python"]},
            {"apollo_id": "a1", "domain": "acme.com", "tech_stack": ["React"]},
        ]
        result = deduplicate_companies(companies)
        assert len(result) == 1
        assert set(result[0]["tech_stack"]) == {"Python", "React"}

    def test_preserves_unique(self):
        companies = [
            {"apollo_id": "a1", "domain": "acme.com"},
            {"apollo_id": "a2", "domain": "beta.com"},
        ]
        result = deduplicate_companies(companies)
        assert len(result) == 2


class TestDeduplicateMessages:
    def test_removes_duplicates(self):
        messages = [
            {"campaign_id": "c1", "contact_id": "ct1", "channel": "email", "sent_at": "2026-01-01"},
            {"campaign_id": "c1", "contact_id": "ct1", "channel": "email", "sent_at": "2026-01-02"},
        ]
        result = deduplicate_messages(messages)
        assert len(result) == 1
        assert result[0]["sent_at"] == "2026-01-02"  # keeps latest

    def test_different_channels_kept(self):
        messages = [
            {"campaign_id": "c1", "contact_id": "ct1", "channel": "email"},
            {"campaign_id": "c1", "contact_id": "ct1", "channel": "linkedin"},
        ]
        result = deduplicate_messages(messages)
        assert len(result) == 2
