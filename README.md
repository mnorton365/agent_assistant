AGENT ASSISTANT

OVERVIEW
This project is an exploration into data ingestion pipelines and AI-enabled data engineering.
Currently, it is setup to read synthetic policy JSON documents for ingestion, including
normalization and validation procedures.

CURRENT CAPABILITIES
* Schema validation against Pydantic data model
* Timestamp validation w/UTC normalization
* Text normalization
* Duplicate document ID detection
* Separation of accepted & rejected datasets
* Deterministic output serialization and sorting
* Automated testing w/pytest

REQUIREMENTS
* Python v3.13.14
* Git (if cloning)
* Core Packages available in requirements.txt

ARCHITECTURE (INGESTION)
1) Discover JSON files & repositories
2) Open & Read files
3) Validate records against Pydantic's SourceDocument schema
4) Detect duplicate document IDs
5) Normalize validated, unique documents
6) Calculate SHA-256 fingerprints of standardized, serialized text
7) Classify documents as Accepted & Rejected
8) Separate & Sort documents into 2x JSONL outputs w/ingestion summary reporting

DATA STORAGE
* By default, data inputs are stored in data/raw and data outputs are stored in data/processed.
* Data outputs include JSONL files for documents that passed and failed the validation process.

EXECUTION COMMANDS
* python src/ingest.py      # Execute ingestion pipeline
    o Optional Arguments: raw, output
* python -m pytest -q       # Run testing policies