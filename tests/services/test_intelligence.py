"""Intelligence service tests."""

from services.intelligence import assign_contact_segment, _rule_based_classification


class TestAssignContactSegment:
    def test_vp_is_decision_maker(self):
        result = assign_contact_segment({"seniority": "vp", "title": "VP Engineering"})
        assert result["segment"] == "decision_maker"
        assert result["seniority_group"] == "executive"

    def test_director_is_decision_maker(self):
        result = assign_contact_segment({"seniority": "director", "title": "Director of Engineering"})
        assert result["segment"] == "decision_maker"

    def test_manager_is_influencer(self):
        result = assign_contact_segment({"seniority": "manager", "title": "Engineering Manager"})
        assert result["segment"] == "influencer"
        assert result["seniority_group"] == "manager"

    def test_ic_is_implementer(self):
        result = assign_contact_segment({"seniority": "individual_contributor", "title": "Software Engineer"})
        assert result["segment"] == "implementer"

    def test_cto_title_override(self):
        result = assign_contact_segment({"seniority": "other", "title": "CTO"})
        assert result["segment"] == "decision_maker"

    def test_engineering_department_boost(self):
        base = assign_contact_segment({"seniority": "manager", "department": "sales"})
        boosted = assign_contact_segment({"seniority": "manager", "department": "engineering"})
        assert boosted["decision_maker_score"] > base["decision_maker_score"]

    def test_unknown_seniority(self):
        result = assign_contact_segment({"seniority": "unknown"})
        assert result["segment"] == "other"


class TestRuleBasedClassification:
    def test_high_fit_midsize(self):
        result = _rule_based_classification({"employee_count": 500, "industry": "Tech"})
        assert result["classification"] == "high-fit"

    def test_moderate_fit_large(self):
        result = _rule_based_classification({"employee_count": 8000, "industry": "Finance"})
        assert result["classification"] == "moderate-fit"

    def test_low_fit_tiny(self):
        result = _rule_based_classification({"employee_count": 5, "industry": "Other"})
        assert result["classification"] == "low-fit"
