from __future__ import annotations

DEFAULT_SCHEMA = {
  "type": "object",
  "required": ["meeting", "summary", "decisions", "todos", "topics", "open_questions"],
  "properties": {
    "meeting": {
      "type": "object",
      "required": ["title", "date", "participants"],
      "properties": {
        "title": {"type": "string"},
        "date": {"type": "string"},
        "participants": {"type": "array", "items": {"type": "string"}}
      }
    },
    "summary": {"type": "array", "items": {"type": "string"}},
    "decisions": {
      "type": "array",
      "items": {
        "oneOf": [
          {"type": "string"},
          {
            "type": "object",
            "required": ["text"],
            "properties": {
              "text": {"type": "string"},
              "timestamp": {"type": "string"},
              "evidence": {"type": "string"}
            }
          }
        ]
      }
    },
    "todos": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["owner", "task", "due"],
        "properties": {
          "owner": {"type": "string"},
          "task": {"type": "string"},
          "due": {"type": "string"},
          "timestamp": {"type": "string"},
          "evidence": {"type": "string"}
        }
      }
    },
    "topics": {"type": "array", "items": {"type": "string"}},
    "open_questions": {"type": "array", "items": {"type": "string"}},
    "next_steps": {"type": "array", "items": {"type": "string"}},
    "notes": {"type": "string"}
  }
}
