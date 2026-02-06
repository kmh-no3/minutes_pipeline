"""
Test Pydantic schema validation for minutes JSON.
Tests the validate_minutes_json() function and model normalization.
"""

import logging
import pytest
from minutes_pipeline.summarize.models import (
    validate_minutes_json,
    MinutesModel,
    SummaryModel,
    MeetingModel,
    DecisionModel,
    TodoModel,
)


class TestSummaryModel:
    """Test SummaryModel validation and normalization."""

    def test_string_overview_passes(self):
        """Test that string overview is accepted."""
        summary = SummaryModel(overview="This is an overview", highlights=["point1"])
        assert summary.overview == "This is an overview"
        assert summary.highlights == ["point1"]

    def test_list_overview_normalized_to_string(self, caplog):
        """Test that list overview is normalized to newline-joined string."""
        with caplog.at_level(logging.WARNING):
            summary = SummaryModel(overview=["line1", "line2", "line3"], highlights=["point1"])
        
        assert summary.overview == "line1\nline2\nline3"
        assert summary.highlights == ["point1"]
        assert "array; normalized" in caplog.text

    def test_none_overview_becomes_empty_string(self):
        """Test that None overview becomes empty string."""
        summary = SummaryModel(overview=None, highlights=["point1"])
        assert summary.overview == ""
        assert summary.highlights == ["point1"]

    def test_dict_overview_converted_to_string(self, caplog):
        """Test that dict overview is converted to string."""
        with caplog.at_level(logging.WARNING):
            summary = SummaryModel(overview={"nested": "data"}, highlights=[])
        
        assert isinstance(summary.overview, str)
        assert "dict" in caplog.text

    def test_empty_highlights_defaults(self):
        """Test that missing highlights defaults to empty list."""
        summary = SummaryModel(overview="Overview")
        assert summary.highlights == []


class TestMeetingModel:
    """Test MeetingModel validation and normalization."""

    def test_valid_meeting(self):
        """Test valid meeting data."""
        meeting = MeetingModel(
            title="Test Meeting",
            date="2024-01-01",
            participants=["Alice", "Bob"]
        )
        assert meeting.title == "Test Meeting"
        assert meeting.date == "2024-01-01"
        assert meeting.participants == ["Alice", "Bob"]

    def test_participants_string_normalized_to_list(self):
        """Test that string participant is normalized to list."""
        meeting = MeetingModel(title="Test", date="2024-01-01", participants="Alice")
        assert meeting.participants == ["Alice"]

    def test_participants_dict_extracts_name(self):
        """Test that dict participants extract name field."""
        meeting = MeetingModel(
            title="Test",
            date="2024-01-01",
            participants=[{"name": "Alice"}, {"role": "Bob"}]
        )
        assert meeting.participants == ["Alice", "Bob"]


class TestDecisionModel:
    """Test DecisionModel validation."""

    def test_valid_decision(self):
        """Test valid decision data."""
        decision = DecisionModel(
            text="We decided to proceed",
            timestamp="00:12:34",
            evidence="Quote from meeting"
        )
        assert decision.text == "We decided to proceed"
        assert decision.timestamp == "00:12:34"
        assert decision.evidence == "Quote from meeting"

    def test_minimal_decision(self):
        """Test decision with only text."""
        decision = DecisionModel(text="Simple decision")
        assert decision.text == "Simple decision"
        assert decision.timestamp == ""
        assert decision.evidence == ""


class TestTodoModel:
    """Test TodoModel validation."""

    def test_valid_todo(self):
        """Test valid todo data."""
        todo = TodoModel(
            owner="Alice",
            task="Complete the report",
            due="2024-12-31",
            timestamp="00:15:00",
            evidence="Mentioned in discussion"
        )
        assert todo.owner == "Alice"
        assert todo.task == "Complete the report"
        assert todo.due == "2024-12-31"

    def test_minimal_todo(self):
        """Test todo with empty optional fields."""
        todo = TodoModel(owner="", task="Task", due="")
        assert todo.owner == ""
        assert todo.task == "Task"
        assert todo.due == ""


class TestMinutesModel:
    """Test MinutesModel validation and normalization."""

    def test_valid_minutes_with_dict_summary(self):
        """Test valid minutes with dict summary."""
        data = {
            "meeting": {"title": "Test", "date": "2024-01-01", "participants": ["Alice"]},
            "summary": {"overview": "Overview text", "highlights": ["point1"]},
            "decisions": [{"text": "Decision 1"}],
            "todos": [{"owner": "Alice", "task": "Task 1", "due": "2024-12-31"}],
            "topics": ["topic1"],
            "open_questions": ["question1"],
            "next_steps": ["step1"],
            "notes": "Some notes",
        }
        minutes = MinutesModel(**data)
        assert isinstance(minutes.summary, SummaryModel)
        assert minutes.summary.overview == "Overview text"

    def test_valid_minutes_with_list_summary(self):
        """Test valid minutes with list summary."""
        data = {
            "meeting": {"title": "Test", "date": "2024-01-01", "participants": ["Alice"]},
            "summary": ["summary1", "summary2"],
            "decisions": [],
            "todos": [],
            "topics": [],
            "open_questions": [],
        }
        minutes = MinutesModel(**data)
        assert isinstance(minutes.summary, list)
        assert minutes.summary == ["summary1", "summary2"]

    def test_minutes_with_list_overview_in_dict_summary(self, caplog):
        """Test minutes where summary.overview is a list (the bug case)."""
        data = {
            "meeting": {"title": "Test", "date": "2024-01-01", "participants": ["Alice"]},
            "summary": {"overview": ["line1", "line2"], "highlights": ["point1"]},
            "decisions": [],
            "todos": [],
            "topics": [],
            "open_questions": [],
        }
        with caplog.at_level(logging.WARNING):
            minutes = MinutesModel(**data)
        
        assert isinstance(minutes.summary, SummaryModel)
        assert minutes.summary.overview == "line1\nline2"
        assert "array; normalized" in caplog.text

    def test_to_dict_conversion(self):
        """Test to_dict() method converts models back to dict."""
        data = {
            "meeting": {"title": "Test", "date": "2024-01-01", "participants": ["Alice"]},
            "summary": {"overview": "Overview", "highlights": ["point1"]},
            "decisions": [{"text": "Decision 1"}],
            "todos": [{"owner": "Alice", "task": "Task 1", "due": "2024-12-31"}],
            "topics": ["topic1"],
            "open_questions": [],
            "next_steps": [],
            "notes": "",
        }
        minutes = MinutesModel(**data)
        result = minutes.to_dict()
        
        assert isinstance(result, dict)
        assert isinstance(result["meeting"], dict)
        assert result["meeting"]["title"] == "Test"
        assert isinstance(result["summary"], dict)
        assert result["summary"]["overview"] == "Overview"
        assert isinstance(result["decisions"][0], dict)
        assert result["decisions"][0]["text"] == "Decision 1"

    def test_decisions_string_format(self):
        """Test decisions can be strings."""
        data = {
            "meeting": {"title": "Test", "date": "2024-01-01", "participants": []},
            "summary": [],
            "decisions": ["Decision as string", {"text": "Decision as object"}],
            "todos": [],
            "topics": [],
            "open_questions": [],
        }
        minutes = MinutesModel(**data)
        assert len(minutes.decisions) == 2
        assert minutes.decisions[0] == "Decision as string"
        assert isinstance(minutes.decisions[1], DecisionModel)


class TestValidateMinutesJson:
    """Test validate_minutes_json() function."""

    def test_valid_json_returns_model_and_no_warnings(self):
        """Test that valid JSON returns model with no warnings."""
        data = {
            "meeting": {"title": "Test", "date": "2024-01-01", "participants": ["Alice"]},
            "summary": {"overview": "Overview", "highlights": []},
            "decisions": [],
            "todos": [],
            "topics": [],
            "open_questions": [],
        }
        model, warnings = validate_minutes_json(data)
        
        assert isinstance(model, MinutesModel)
        assert len(warnings) == 0

    def test_json_with_list_overview_returns_model_with_normalization(self, caplog):
        """Test that JSON with list overview is normalized."""
        data = {
            "meeting": {"title": "Test", "date": "2024-01-01", "participants": []},
            "summary": {"overview": ["line1", "line2"], "highlights": []},
            "decisions": [],
            "todos": [],
            "topics": [],
            "open_questions": [],
        }
        with caplog.at_level(logging.WARNING):
            model, warnings = validate_minutes_json(data)
        
        assert isinstance(model, MinutesModel)
        assert isinstance(model.summary, SummaryModel)
        assert model.summary.overview == "line1\nline2"
        assert "array; normalized" in caplog.text

    def test_minimal_valid_json(self):
        """Test minimal valid JSON with defaults."""
        data = {
            "meeting": {"title": "", "date": "", "participants": []},
            "summary": [],
            "decisions": [],
            "todos": [],
            "topics": [],
            "open_questions": [],
        }
        model, warnings = validate_minutes_json(data)
        
        assert isinstance(model, MinutesModel)
        assert len(warnings) == 0

    def test_empty_dict_uses_defaults(self):
        """Test that empty dict uses model defaults."""
        data = {}
        model, warnings = validate_minutes_json(data)
        
        assert isinstance(model, MinutesModel)
        # Should have default values
        assert isinstance(model.meeting, (MeetingModel, dict))
        assert isinstance(model.summary, (list, SummaryModel, dict))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
