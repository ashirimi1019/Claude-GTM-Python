"""Apollo.io client module — company search, contact enrichment, sequences, analytics."""

from clients.apollo.analytics import get_contact_activity_log, get_sequence_analytics
from clients.apollo.contacts import batch_enrich_contacts, enrich_contact, search_decision_makers
from clients.apollo.enrichment import (
    batch_enrich_organizations,
    enrich_organization_by_domain,
    merge_enriched_data,
)
from clients.apollo.errors import ApolloError, handle_apollo_error
from clients.apollo.search import search_companies
from clients.apollo.sequences import (
    activate_sequence,
    add_email_step,
    create_sequence,
    enroll_sequence,
    get_email_accounts,
    pause_sequence,
    remove_contacts_from_sequence,
)
from clients.apollo.types import (
    ApolloCompany,
    ApolloContact,
    ApolloOrgEnrichmentResult,
    ApolloQueryParams,
    ApolloSearchResponse,
)
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
