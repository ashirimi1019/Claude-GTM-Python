"""Tests for core/guardrails/validators.py — Tier 2 and Tier 3 copy validation."""

from core.guardrails.validators import validate_copy_tier2, validate_copy_tier3


class TestValidateCopyTier2:
    def test_valid_copy_passes(self):
        variant = {
            "subject": "Quick question about {companyName}",
            "body": "Hi {firstName}, I noticed {companyName} is hiring data engineers.",
        }
        result = validate_copy_tier2(variant)
        assert result["valid"] is True
        assert result["errors"] == []
        assert result["tier"] == 2

    def test_body_exceeds_2000_chars(self):
        variant = {"body": "x" * 2001, "subject": "ok"}
        result = validate_copy_tier2(variant)
        assert result["valid"] is False
        assert any("2000 character" in e for e in result["errors"])

    def test_subject_exceeds_200_chars(self):
        variant = {"body": "ok", "subject": "s" * 201}
        result = validate_copy_tier2(variant)
        assert result["valid"] is False
        assert any("200 character" in e for e in result["errors"])

    def test_unknown_placeholders_flagged(self):
        variant = {"body": "Hello {firstName}, your {unknownField} is great", "subject": "Hi"}
        result = validate_copy_tier2(variant)
        assert result["valid"] is False
        assert any("Unknown placeholders" in e for e in result["errors"])

    def test_allowed_placeholders_pass(self):
        variant = {
            "body": "{firstName} {lastName} at {companyName} ({title}) in {industry} - {signal} for {campaignName}",
            "subject": "Hi",
        }
        result = validate_copy_tier2(variant)
        assert result["valid"] is True

    def test_hallucination_marker_detected(self):
        variant = {"body": "As an AI language model, I think this is great", "subject": "Hi"}
        result = validate_copy_tier2(variant)
        assert result["valid"] is False
        assert any("Hallucination marker" in e for e in result["errors"])

    def test_hallucination_i_cannot(self):
        variant = {"body": "I cannot verify this claim but here goes", "subject": ""}
        result = validate_copy_tier2(variant)
        assert result["valid"] is False
        assert any("i cannot" in e.lower() for e in result["errors"])

    def test_hallucination_based_on_training(self):
        variant = {"body": "Based on my training data, companies like yours...", "subject": ""}
        result = validate_copy_tier2(variant)
        assert result["valid"] is False

    def test_empty_body_passes(self):
        variant = {"body": "", "subject": ""}
        result = validate_copy_tier2(variant)
        assert result["valid"] is True

    def test_multiple_errors_returned(self):
        variant = {"body": "x" * 2001 + " as an ai {badPlaceholder}", "subject": "s" * 201}
        result = validate_copy_tier2(variant)
        assert result["valid"] is False
        # body length + subject length + hallucination (placeholder may be in overflow)
        assert len(result["errors"]) >= 3


class TestValidateCopyTier3:
    def test_clean_copy_needs_no_approval(self):
        variant = {"body": "Hi, I noticed your team is growing. Would love to chat."}
        result = validate_copy_tier3(variant)
        assert result["needs_approval"] is False
        assert result["flags"] == []
        assert result["tier"] == 3

    def test_aggressive_cta_act_now(self):
        variant = {"body": "Act now before this opportunity disappears!"}
        result = validate_copy_tier3(variant)
        assert result["needs_approval"] is True
        assert any("act now" in f.lower() for f in result["flags"])

    def test_aggressive_cta_limited_time(self):
        variant = {"body": "This is a limited time offer for your team."}
        result = validate_copy_tier3(variant)
        assert result["needs_approval"] is True
        assert any("limited time" in f.lower() for f in result["flags"])

    def test_aggressive_cta_dont_miss_out(self):
        variant = {"body": "Don't miss out on this amazing deal."}
        result = validate_copy_tier3(variant)
        assert result["needs_approval"] is True

    def test_aggressive_cta_urgent(self):
        variant = {"body": "This is urgent - we need to talk."}
        result = validate_copy_tier3(variant)
        assert result["needs_approval"] is True

    def test_competitor_mention_flagged(self):
        variant = {"body": "We're better than the competitor tools you're using."}
        result = validate_copy_tier3(variant)
        assert result["needs_approval"] is True
        assert any("Competitor" in f for f in result["flags"])

    def test_versus_flagged(self):
        variant = {"body": "Our platform vs theirs - see the difference."}
        result = validate_copy_tier3(variant)
        assert result["needs_approval"] is True

    def test_multiple_flags(self):
        variant = {"body": "Act now! We're better than the competitor. Limited time!"}
        result = validate_copy_tier3(variant)
        assert result["needs_approval"] is True
        assert len(result["flags"]) >= 3

    def test_empty_body_clean(self):
        variant = {"body": ""}
        result = validate_copy_tier3(variant)
        assert result["needs_approval"] is False
