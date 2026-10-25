import argparse
import hashlib
import json

from pathlib import Path
from pydantic import ValidationError
from typing import Any
from validate import SourceDocument

def sha256_text(text: str):
    # Purpose: Returns a SHA-256 hash of the UTF-8 text.
    return hashlib.sha256(text.encode("UTF-8")).hexdigest()

def write_jsonl(path: Path, records: list[dict[str, Any]]):
    # Purpose: Writes records to deterministic JSON Lines.

    # Verifies output folder's existence (creates folder if missing)
    path.parent.mkdir(parents = True, exist_ok = True)

    # Writes input records into master JSON array
    with path.open("w", encoding = "UTF-8", newline = "\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii = False, sort_keys = True) + "\n")

def ingest(raw_dir: Path, output_dir: Path):
    # Purpose: Validates source documents to produce accepted and rejected datasets.

    # Resolve input / output directory paths for reliability
    raw_dir = raw_dir.resolve()
    output_dir = output_dir.resolve()

    # Error Check: Directory exists
    if not raw_dir.is_dir():
        raise FileNotFoundError(f"Raw directory not found: {raw_dir}.")

    # Error Check: Directories aren't synonymous
    if raw_dir == output_dir or raw_dir in output_dir.parents:
        raise ValueError("Output directory must be outside input directory.")

    # Establish output dataset & TBD TBD TBD
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    duplicate_count = 0

    # Execute ingestion and validation pipeline
    for path in sorted(raw_dir.glob("*.json")):
        try:
            # Opens, Reads, and Validates the raw files
            with path.open("r", encoding = "UTF-8") as file:
                raw_record = json.load(file)
            document = SourceDocument.model_validate(raw_record)

            # Duplicate Check
            if document.document_id in seen_ids:
                duplicate_count += 1
                raise ValueError(f"Duplicate document_id: {document.document_id}")
            seen_ids.add(document.document_id)

            # Convert document objects into JSON strings
            canonical_text = json.dumps(
                    document.model_dump(mode = "json"),
                    ensure_ascii = False,
                    sort_keys = True)
            
            # Create Accepted dictionary dataset w/SHA-256 hash
            accepted.append({
                **document.model_dump(mode="json"),
                "source_file": path.name,
                "content_sha256": sha256_text(canonical_text)})
        
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError, ValueError) as exc:
            # Create Rejected dictionary if 1x of 4x Errors occurs
            rejected.append({
                "source_file": path.name,
                "error": str(exc)})
    
    # Sort & Return 2x datasets
    accepted.sort(key = lambda item: item["document_id"])
    rejected.sort(key = lambda item: item["source_file"])
    return {
        "files_seen": len(list(raw_dir.glob("*.json"))),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "duplicates": duplicate_count}

def main():
    # Provide help documentation
    parser = argparse.ArgumentParser(
        description = "Purpose: Validate & ingest synthetic policy documents.")
    
    # Creates raw argument
    parser.add_argument(
        "--raw",
        type = Path,
        default = Path("data/raw"),
        help = "Directory containing source JSON files.")
    
    # Creates output argument
    parser.add_argument(
        "--output",
        type = Path,
        default = Path("data/processed"),
        help = "Directory for generated JSONL files.")
    
    # Adds arguments to parser
    args = parser.parse_args()

    # Executes ingestion pipeline and establishes print summary w/2x Error Checks
    try:
        summary = ingest(args.raw, args.output)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")
    
    # Prints execution summary
    print("Ingestion Complete!")
    for key, value in summary.items():
        print(f"{key}: {value}")



# MAIN EXECUTION
if __name__ == "__main__":
    main()