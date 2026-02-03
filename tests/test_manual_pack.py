from pathlib import Path
import json

from minutes_pipeline.config import load_config
from minutes_pipeline.pipeline import request_pack

def test_request_pack_creates_files(tmp_path: Path):
    (tmp_path/"prompts").mkdir()
    (tmp_path/"prompts"/"minutes_prompt.md").write_text("JSONで要約してください。", encoding="utf-8")
    (tmp_path/"prompts"/"minutes_schema.json").write_text(json.dumps({
        "type":"object",
        "required":["meeting","summary","decisions","todos","topics","open_questions"],
        "properties":{}
    }, ensure_ascii=False), encoding="utf-8")
    (tmp_path/"minutes.yml").write_text("""
summarize:
  engine: manual
  prompt_path: prompts/minutes_prompt.md
  schema_path: prompts/minutes_schema.json
""", encoding="utf-8")

    # transcript
    run_dir = tmp_path/"output"
    run_dir.mkdir()
    t = {"language":"ja", "segments":[{"start":0.0,"end":1.0,"speaker":None,"text":"テストです。"}]}
    (run_dir/"transcript_clean.json").write_text(json.dumps(t, ensure_ascii=False), encoding="utf-8")

    request_pack(run_dir/"transcript_clean.json", tmp_path/"minutes.yml")
    assert (run_dir/"llm_instructions.md").exists()
    assert (run_dir/"llm_transcript.txt").exists()
