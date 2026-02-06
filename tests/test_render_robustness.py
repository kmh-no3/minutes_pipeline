"""
Test render.py robustness against type variations in LLM output.
Tests the _to_text() function and _summary_to_strings() handling of various input types.
"""

import pytest
from minutes_pipeline.summarize.render import (
    _to_text,
    _summary_to_strings,
    render_minutes_md,
)


class TestToText:
    """Test _to_text() helper function."""

    def test_none_returns_empty_string(self):
        """Test that None is converted to empty string."""
        assert _to_text(None) == ""

    def test_string_returns_as_is(self):
        """Test that string is returned as-is."""
        assert _to_text("hello") == "hello"
        assert _to_text("  spaced  ") == "  spaced  "

    def test_list_joins_with_newlines(self):
        """Test that list items are joined with newlines."""
        assert _to_text(["item1", "item2", "item3"]) == "item1\nitem2\nitem3"
        assert _to_text(["  spaced  ", "item"]) == "spaced\nitem"

    def test_list_filters_empty_items(self):
        """Test that empty list items are filtered out."""
        assert _to_text(["item1", "", "item2", "  ", "item3"]) == "item1\nitem2\nitem3"
        assert _to_text(["", "  ", ""]) == ""

    def test_dict_converts_to_string(self):
        """Test that dict is converted to string representation."""
        result = _to_text({"key": "value"})
        assert isinstance(result, str)
        assert "key" in result
        assert "value" in result

    def test_other_types_convert_to_string(self):
        """Test that other types are converted to string."""
        assert _to_text(123) == "123"
        assert _to_text(45.67) == "45.67"
        assert _to_text(True) == "True"


class TestSummaryToStrings:
    """Test _summary_to_strings() with various input types."""

    def test_none_returns_empty_list(self):
        """Test that None returns empty list."""
        assert _summary_to_strings(None) == []

    def test_empty_list_returns_empty_list(self):
        """Test that empty list returns empty list."""
        assert _summary_to_strings([]) == []

    def test_list_of_strings_returns_as_is(self):
        """Test that list of strings is returned as-is (stripped)."""
        result = _summary_to_strings(["item1", "item2", "item3"])
        assert result == ["item1", "item2", "item3"]

    def test_list_filters_empty_strings(self):
        """Test that empty strings are filtered from list."""
        result = _summary_to_strings(["item1", "", "  ", "item2"])
        assert result == ["item1", "item2"]

    def test_dict_with_string_overview(self):
        """Test dict with string overview (normal case)."""
        summary = {"overview": "This is an overview", "highlights": ["point1", "point2"]}
        result = _summary_to_strings(summary)
        assert result == ["This is an overview", "point1", "point2"]

    def test_dict_with_list_overview(self):
        """Test dict with list overview (the bug case) - should not crash."""
        summary = {"overview": ["line1", "line2", "line3"], "highlights": ["point1"]}
        result = _summary_to_strings(summary)
        # Should join list items with newlines and include as single item
        assert len(result) == 2
        assert result[0] == "line1\nline2\nline3"
        assert result[1] == "point1"

    def test_dict_with_none_overview(self):
        """Test dict with None overview."""
        summary = {"overview": None, "highlights": ["point1", "point2"]}
        result = _summary_to_strings(summary)
        assert result == ["point1", "point2"]

    def test_dict_with_dict_overview(self):
        """Test dict with dict overview (edge case) - should not crash."""
        summary = {"overview": {"nested": "data"}, "highlights": ["point1"]}
        result = _summary_to_strings(summary)
        # Should convert dict to string
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert "nested" in result[0]
        assert result[1] == "point1"

    def test_dict_with_empty_overview(self):
        """Test dict with empty string overview."""
        summary = {"overview": "", "highlights": ["point1"]}
        result = _summary_to_strings(summary)
        assert result == ["point1"]

    def test_dict_without_overview_key(self):
        """Test dict without overview key."""
        summary = {"highlights": ["point1", "point2"]}
        result = _summary_to_strings(summary)
        assert result == ["point1", "point2"]

    def test_dict_with_empty_highlights(self):
        """Test dict with empty highlights."""
        summary = {"overview": "Overview text", "highlights": []}
        result = _summary_to_strings(summary)
        assert result == ["Overview text"]

    def test_dict_with_none_highlights(self):
        """Test dict with None highlights."""
        summary = {"overview": "Overview text", "highlights": None}
        result = _summary_to_strings(summary)
        assert result == ["Overview text"]

    def test_plain_string_returns_as_list(self):
        """Test that plain string is wrapped in list."""
        result = _summary_to_strings("plain text")
        assert result == ["plain text"]


class TestRenderMinutesMd:
    """Test render_minutes_md() with various summary formats."""

    def test_render_with_list_overview_in_summary_dict(self):
        """Test that rendering doesn't crash when overview is a list."""
        minutes = {
            "meeting": {"title": "Test Meeting", "date": "2024-01-01", "participants": ["Alice"]},
            "summary": {"overview": ["line1", "line2"], "highlights": ["point1"]},
            "decisions": [],
            "todos": [],
            "topics": [],
            "open_questions": [],
            "notes": "",
        }
        # Should not raise AttributeError
        result = render_minutes_md(minutes)
        assert isinstance(result, str)
        assert "line1" in result
        assert "line2" in result
        assert "point1" in result

    def test_render_with_string_overview(self):
        """Test normal case with string overview."""
        minutes = {
            "meeting": {"title": "Test Meeting", "date": "2024-01-01", "participants": ["Alice"]},
            "summary": {"overview": "Normal overview", "highlights": ["point1"]},
            "decisions": [],
            "todos": [],
            "topics": [],
            "open_questions": [],
            "notes": "",
        }
        result = render_minutes_md(minutes)
        assert isinstance(result, str)
        assert "Normal overview" in result
        assert "point1" in result

    def test_render_with_none_overview(self):
        """Test with None overview."""
        minutes = {
            "meeting": {"title": "Test Meeting", "date": "2024-01-01", "participants": ["Alice"]},
            "summary": {"overview": None, "highlights": ["point1"]},
            "decisions": [],
            "todos": [],
            "topics": [],
            "open_questions": [],
            "notes": "",
        }
        result = render_minutes_md(minutes)
        assert isinstance(result, str)
        assert "point1" in result

    def test_render_with_dict_overview(self):
        """Test with dict overview (edge case)."""
        minutes = {
            "meeting": {"title": "Test Meeting", "date": "2024-01-01", "participants": ["Alice"]},
            "summary": {"overview": {"nested": "data"}, "highlights": []},
            "decisions": [],
            "todos": [],
            "topics": [],
            "open_questions": [],
            "notes": "",
        }
        # Should not crash
        result = render_minutes_md(minutes)
        assert isinstance(result, str)

    def test_render_with_list_summary(self):
        """Test with summary as list (alternative format)."""
        minutes = {
            "meeting": {"title": "Test Meeting", "date": "2024-01-01", "participants": ["Alice"]},
            "summary": ["summary1", "summary2"],
            "decisions": [],
            "todos": [],
            "topics": [],
            "open_questions": [],
            "notes": "",
        }
        result = render_minutes_md(minutes)
        assert isinstance(result, str)
        assert "summary1" in result
        assert "summary2" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
