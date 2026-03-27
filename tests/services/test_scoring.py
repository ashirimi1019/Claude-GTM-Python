"""Legacy scoring service tests."""

from services.scoring import (
    DEFAULT_SCORING_CONFIG,
    parse_scoring_config,
    resolve_scoring_config,
)


class TestParseScoringConfig:
    def test_empty_md_returns_defaults(self):
        config = parse_scoring_config("")
        assert config["strictness"] == "broad"
        assert config["threshold"] == 75

    def test_parses_yaml_block(self):
        md = """# Scoring Config

```yaml
strictness: balanced
threshold: 115
preferred_tech:
  - Python
  - React
```

Some text after.
"""
        config = parse_scoring_config(md)
        assert config["strictness"] == "balanced"
        assert config["threshold"] == 115
        assert "Python" in config["preferred_tech"]

    def test_multiple_yaml_blocks_merged(self):
        md = """
```yaml
strictness: strict
```

```yaml
threshold: 165
```
"""
        config = parse_scoring_config(md)
        assert config["strictness"] == "strict"
        assert config["threshold"] == 165

    def test_invalid_yaml_skipped(self):
        md = """
```yaml
this is not: valid: yaml: {{{{
```
"""
        config = parse_scoring_config(md)
        assert config == DEFAULT_SCORING_CONFIG


class TestResolveScoringConfig:
    def test_defaults_when_nothing_provided(self):
        config = resolve_scoring_config()
        assert config == DEFAULT_SCORING_CONFIG

    def test_vertical_overrides_defaults(self):
        md = """
```yaml
strictness: balanced
```
"""
        config = resolve_scoring_config(vertical_scoring_md=md)
        assert config["strictness"] == "balanced"

    def test_offer_overrides_vertical(self):
        md = """
```yaml
strictness: balanced
```
"""
        config = resolve_scoring_config(
            vertical_scoring_md=md,
            offer_overrides={"strictness": "strict"},
        )
        assert config["strictness"] == "strict"

    def test_campaign_overrides_all(self):
        config = resolve_scoring_config(
            vertical_scoring_md="",
            offer_overrides={"strictness": "strict"},
            campaign_overrides={"strictness": "very_strict"},
        )
        assert config["strictness"] == "very_strict"

    def test_partial_overrides_preserve_defaults(self):
        config = resolve_scoring_config(
            offer_overrides={"preferred_tech": ["Python"]},
        )
        assert config["preferred_tech"] == ["Python"]
        assert config["threshold"] == 75  # default preserved
