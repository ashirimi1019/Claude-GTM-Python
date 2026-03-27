"""Apollo.io client module — company search, contact enrichment, sequences, analytics."""

from clients.apollo.search import search_companies
from clients.apollo.contacts import search_decision_makers, enrich_contact, batch_enrich_contacts
from clients.apollo.enrichment import (
    enrich_organization_by_domain,
    batch_enrich_organizations,
    merge_enriched_data,
)
from clients.apollo.sequences import (
    create_sequence,
    add_email_step,
    activate_sequence,
    enroll_sequence,
    pause_sequence,
    remove_contacts_from_sequence,
    get_email_accounts,
)
from clients.apollo.analytics import get_sequence_analytics, get_contact_activity_log
from clients.apollo.types import (
    ApolloCompany,
    ApolloContact,
    ApolloQueryParams,
    ApolloSearchResponse,
    ApolloOrgEnrichmentResult,
)
from clients.apollo.errors import ApolloError, handle_apollo_error
from clients.apollo.utils import normalize_domain

__all__ = [
    "search_companies",
    "search_decision_makers",
    "enrich_contact",
    "batch_enrich_contacts",
    "enrich_organization_by_domain",
    "batch_enrich_organizations",
    "merge_enriched_data",
    "create_sequence",
    "add_email_step",
    "activate_sequence",
    "enroll_sequence",
    "pause_sequence",
    "remove_contacts_from_sequence",
    "get_email_accounts",
    "get_sequence_analytics",
    "get_contact_activity_log",
    "normalize_domain",
    "ApolloCompany",
    "ApolloContact",
    "ApolloQueryParams",
    "ApolloSearchResponse",
    "ApolloOrgEnrichmentResult",
    "ApolloError",
    "handle_apollo_error",
]
