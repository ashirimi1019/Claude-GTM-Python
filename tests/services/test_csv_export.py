"""CSV export service tests."""

import csv
from pathlib import Path

from services.csv_export import (
    export_companies_to_csv,
    export_contacts_to_csv,
    export_messages_to_csv,
)


class TestExportCompaniesToCsv:
    def test_creates_file(self, tmp_path):
        companies = [
            {"company_id": "1", "name": "Acme", "domain": "acme.com", "icp_score": 180},
        ]
        filepath = export_companies_to_csv(companies, tmp_path / "companies.csv")
        assert filepath.exists()

    def test_has_headers(self, tmp_path):
        companies = [{"name": "Acme", "domain": "acme.com"}]
        filepath = export_companies_to_csv(companies, tmp_path / "companies.csv")
        with open(filepath) as f:
            reader = csv.reader(f)
            headers = next(reader)
        assert "name" in headers
        assert "domain" in headers
        assert "icp_score" in headers

    def test_writes_data(self, tmp_path):
        companies = [
            {"name": "Acme", "domain": "acme.com", "icp_score": 180},
            {"name": "Beta", "domain": "beta.com", "icp_score": 120},
        ]
        filepath = export_companies_to_csv(companies, tmp_path / "companies.csv")
        with open(filepath) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["name"] == "Acme"

    def test_extra_columns(self, tmp_path):
        companies = [{"name": "Acme", "icp_stage1_score": 90}]
        filepath = export_companies_to_csv(
            companies, tmp_path / "companies.csv",
            extra_columns=["icp_stage1_score"],
        )
        with open(filepath) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert rows[0]["icp_stage1_score"] == "90"

    def test_empty_list(self, tmp_path):
        filepath = export_companies_to_csv([], tmp_path / "empty.csv")
        assert filepath.exists()
        with open(filepath) as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 1  # header only


class TestExportContactsToCsv:
    def test_creates_file(self, tmp_path):
        contacts = [{"email": "john@acme.com", "first_name": "John"}]
        filepath = export_contacts_to_csv(contacts, tmp_path / "contacts.csv")
        assert filepath.exists()


class TestExportMessagesToCsv:
    def test_creates_file(self, tmp_path):
        messages = [{"contact_email": "john@acme.com", "subject": "Hello", "channel": "email"}]
        filepath = export_messages_to_csv(messages, tmp_path / "messages.csv")
        assert filepath.exists()
