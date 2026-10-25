import json
import pytest
import sys

from pathlib import Path

# Establish project's src directory path for imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

from ingest import ingest

def create_document(document_id: str):
    # Purpose: Creates a testing document w/fake data.
    return{
        "document_id": document_id,
        "title": f"Policy {document_id}",
        "source": "Synthetic Test Agency",
        "updated_at": "2026-09-15T10:00:00Z",
        "classification": "PUBLIC",
        "text": "   Example   policy text.  "}

def test_ingestion_accepts_valid_record(tmp_path: Path):
    # Establish input & output file paths
    raw = tmp_path / "raw"
    output = tmp_path / "processed"
    raw.mkdir()

    # Create & Ingest testing document
    (raw / "001.json").write_text(
        json.dumps(create_document("POL-001")),
        encoding = "utf-8")
    summary = ingest(raw, output)

    # Verify test conditions
    assert summary["files_seen"] == 1
    assert summary["accepted"] == 1
    assert summary["rejected"] == 0
    record = json.loads((output / "documents.jsonl").read_text(encoding = "utf-8"))
    assert record["document_id"] == "POL-001"
    assert record["text"] == "Example policy text."
    assert len(record["content_sha256"]) == 64

def test_duplicate_id_is_rejected(tmp_path: Path):
    # Establish input & output file paths
    raw = tmp_path / "raw"
    output = tmp_path / "processed"
    raw.mkdir()

    # Create & Ingest testing documents
    for filename in ("001.json", "002.json"):
        (raw / filename).write_text(
            json.dumps(create_document("POL-001")),
            encoding = "utf-8")
    summary = ingest(raw, output)

    # Verify test conditions
    assert summary["accepted"] == 1
    assert summary["rejected"] == 1
    assert summary["duplicates"] == 1

def test_missing_required_field_is_rejected(tmp_path: Path):
    # Establish input & output file paths
    raw = tmp_path / "raw"
    output = tmp_path / "processed"
    raw.mkdir()

    # Create & Ingest testing document
    document = create_document("POL-002")
    del document["text"]
    (raw / "invalid.json").write_text(
        json.dumps(document),
        encoding = "utf-8")
    summary = ingest(raw, output)

    # Verify test conditions
    assert summary["accepted"] == 0
    assert summary["rejected"] == 1
    rejected = json.loads((output / "rejected.jsonl").read_text(encoding = "utf-8"))
    assert rejected["source_file"] == "invalid.json"
    assert "error" in rejected

def test_repeated_runs_produce_identical_output(tmp_path: Path):
    # Establish input & output file paths
    raw = tmp_path / "raw"
    output = tmp_path / "processed"
    raw.mkdir()

    # Create & Ingest testing document
    (raw / "001.json").write_text(
        json.dumps(create_document("POL-001")),
        encoding = "utf-8")
    ingest(raw, output)

    # Verify test conditions
    first_output = (output / "documents.jsonl").read_bytes()
    ingest(raw, output)
    second_output = (output / "documents.jsonl").read_bytes()
    assert first_output == second_output

def test_output_cannot_be_inside_raw_directory(tmp_path: Path):
    # Establish input file path
    raw = tmp_path / "raw"
    raw.mkdir()

    # Verify test conditions
    with pytest.raises(ValueError):
        ingest(raw, raw / "output")

def test_ingestion_writes_accepted_and_rejected_jsonl(tmp_path: Path):
    # Establish input & output file paths
    raw = tmp_path / "raw"
    output = tmp_path / "processed"
    raw.mkdir()

    # Establish valid document
    valid_document = create_document("POL-101")
    (raw / "001_valid.json").write_text(json.dumps(valid_document), encoding = "utf-8")

    # Establish invalid document
    invalid_document = create_document("POL-102")
    del invalid_document["text"]
    (raw / "002_invalid.json").write_text(json.dumps(invalid_document), encoding = "utf-8")

    # Run Ingestion Pipeline
    summary = ingest(raw, output)
    documents_path = output / "documents.jsonl"
    rejected_path = output / "rejected.jsonl"

    # Check both output files exist
    assert documents_path.is_file()
    assert rejected_path.is_file()

    # Check both output files have exactly 1x record
    accepted_lines = documents_path.read_text(encoding = "utf-8").splitlines()
    rejected_lines = rejected_path.read_text(encoding = "utf-8").splitlines()
    assert len(accepted_lines) == 1
    assert len(rejected_lines) == 1

    # Check both output files contain valid JSON objects
    accepted_record = json.loads(accepted_lines[0])
    assert accepted_record["document_id"] == "POL-101"
    assert accepted_record["source_file"] == "001_valid.json"
    assert len(accepted_record["content_sha256"]) == 64

    rejected_record = json.loads(rejected_lines[0])
    assert rejected_record["source_file"] == "002_invalid.json"
    assert "error" in rejected_record

    # Verify summary data
    assert summary == {
        "files_seen": 2,
        "accepted": 1,
        "rejected": 1,
        "duplicates": 0}