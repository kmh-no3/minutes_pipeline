from __future__ import annotations

import logging
from typing import Any, Dict, List, Union

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


class MeetingModel(BaseModel):
    """Meeting metadata model."""
    title: str = ""
    date: str = ""
    participants: List[str] = Field(default_factory=list)

    @field_validator("participants", mode="before")
    @classmethod
    def normalize_participants(cls, v: Any) -> List[str]:
        """Normalize participants to list of strings."""
        if v is None:
            return []
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, str):
                    if item.strip():
                        result.append(item.strip())
                elif isinstance(item, dict):
                    name = (item.get("name") or item.get("role") or "").strip()
                    if name:
                        result.append(name)
                else:
                    result.append(str(item))
            return result
        return []


def _to_text_value(value: Any) -> str:
    """Convert any value to text string."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(str(x).strip() for x in value if str(x).strip())
    if isinstance(value, dict):
        return str(value)
    return str(value)


class DecisionModel(BaseModel):
    """Decision item model."""
    text: str
    timestamp: str = ""
    evidence: str = ""

    @field_validator("text", mode="before")
    @classmethod
    def normalize_text(cls, v: Any) -> str:
        """Normalize text field."""
        if v is None:
            return ""
        return str(v).strip()


class TodoModel(BaseModel):
    """Todo item model."""
    owner: str = ""
    task: str = ""
    due: str = ""
    timestamp: str = ""
    evidence: str = ""

    @field_validator("owner", "task", "due", "timestamp", "evidence", mode="before")
    @classmethod
    def normalize_string_fields(cls, v: Any) -> str:
        """Normalize string fields."""
        if v is None:
            return ""
        return str(v).strip()


class MinutesModel(BaseModel):
    """Main minutes model with validation."""
    meeting: Union[MeetingModel, Dict[str, Any]] = Field(default_factory=dict)
    summary: List[str] = Field(default_factory=list)
    decisions: List[Union[str, DecisionModel, Dict[str, Any]]] = Field(default_factory=list)
    todos: List[Union[TodoModel, Dict[str, Any]]] = Field(default_factory=list)
    topics: List[Union[str, Dict[str, Any]]] = Field(default_factory=list)
    open_questions: List[Union[str, Dict[str, Any]]] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    notes: str = ""

    @field_validator("meeting", mode="before")
    @classmethod
    def normalize_meeting(cls, v: Any) -> Union[MeetingModel, Dict[str, Any]]:
        """Normalize meeting field."""
        if v is None:
            return {}
        if isinstance(v, dict):
            try:
                return MeetingModel(**v)
            except Exception as e:
                logger.warning(f"Failed to validate meeting model: {e}")
                return v
        return {}

    @field_validator("summary", mode="before")
    @classmethod
    def normalize_summary(cls, v: Any) -> List[str]:
        """Normalize summary to list of strings. Handles dict/list/string formats."""
        if v is None:
            return []
        if isinstance(v, str):
            # Single string -> split by newlines
            return [line.strip() for line in v.split("\n") if line.strip()]
        if isinstance(v, list):
            result: List[str] = []
            for item in v:
                text = _to_text_value(item).strip()
                if text:
                    # Split by newlines to get separate items
                    for line in text.split("\n"):
                        if line.strip():
                            result.append(line.strip())
            return result
        if isinstance(v, dict):
            # Handle legacy dict format with overview/highlights
            logger.warning("summary was dict format; converted to array")
            result: List[str] = []
            overview = v.get("overview")
            if overview:
                text = _to_text_value(overview).strip()
                for line in text.split("\n"):
                    if line.strip():
                        result.append(line.strip())
            highlights = v.get("highlights") or v.get("key_points") or []
            if isinstance(highlights, list):
                for h in highlights:
                    text = str(h).strip()
                    if text:
                        result.append(text)
            return result
        return []

    @field_validator("decisions", mode="before")
    @classmethod
    def normalize_decisions(cls, v: Any) -> List[Union[str, DecisionModel, Dict[str, Any]]]:
        """Normalize decisions field."""
        if v is None:
            return []
        if not isinstance(v, list):
            return []
        result = []
        for item in v:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                try:
                    result.append(DecisionModel(**item))
                except Exception:
                    result.append(item)
            else:
                result.append(str(item))
        return result

    @field_validator("todos", mode="before")
    @classmethod
    def normalize_todos(cls, v: Any) -> List[Union[TodoModel, Dict[str, Any]]]:
        """Normalize todos field."""
        if v is None:
            return []
        if not isinstance(v, list):
            return []
        result = []
        for item in v:
            if isinstance(item, dict):
                try:
                    result.append(TodoModel(**item))
                except Exception:
                    result.append(item)
            else:
                # Skip non-dict items for todos
                logger.warning(f"Todo item is not a dict: {type(item).__name__}")
        return result

    @field_validator("topics", "open_questions", mode="before")
    @classmethod
    def normalize_structured_lists(cls, v: Any) -> List[Union[str, Dict[str, Any]]]:
        """Normalize topics/open_questions, preserving dict structure."""
        if v is None:
            return []
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, list):
            result: List[Union[str, Dict[str, Any]]] = []
            for x in v:
                if isinstance(x, dict):
                    # Preserve dict structure
                    result.append(x)
                elif isinstance(x, str):
                    if x.strip():
                        result.append(x.strip())
                else:
                    # Convert other types to string
                    s = str(x).strip()
                    if s:
                        result.append(s)
            return result
        return []

    @field_validator("next_steps", mode="before")
    @classmethod
    def normalize_string_lists(cls, v: Any) -> List[str]:
        """Normalize string list fields."""
        if v is None:
            return []
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        return []

    @field_validator("notes", mode="before")
    @classmethod
    def normalize_notes(cls, v: Any) -> str:
        """Normalize notes field."""
        if v is None:
            return ""
        if isinstance(v, dict):
            import json
            return json.dumps(v, ensure_ascii=False)
        return str(v)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dict, handling nested models."""
        result: Dict[str, Any] = {}
        
        # Meeting
        if isinstance(self.meeting, MeetingModel):
            result["meeting"] = self.meeting.model_dump()
        else:
            result["meeting"] = self.meeting
        
        # Summary (always list of strings now)
        result["summary"] = self.summary
        
        # Decisions
        decisions = []
        for d in self.decisions:
            if isinstance(d, DecisionModel):
                decisions.append(d.model_dump())
            else:
                decisions.append(d)
        result["decisions"] = decisions
        
        # Todos
        todos = []
        for t in self.todos:
            if isinstance(t, TodoModel):
                todos.append(t.model_dump())
            else:
                todos.append(t)
        result["todos"] = todos
        
        # Simple fields
        result["topics"] = self.topics
        result["open_questions"] = self.open_questions
        result["next_steps"] = self.next_steps
        result["notes"] = self.notes
        
        return result


def validate_minutes_json(data: Dict[str, Any]) -> tuple[MinutesModel, List[str]]:
    """
    Validate minutes JSON and return model + warnings.
    
    Returns:
        tuple: (MinutesModel, list of warning messages)
    """
    warnings: List[str] = []
    
    try:
        model = MinutesModel(**data)
        return model, warnings
    except Exception as e:
        warnings.append(f"Validation error: {str(e)}")
        # Try to create a partial model
        try:
            model = MinutesModel()
            return model, warnings
        except Exception:
            raise
