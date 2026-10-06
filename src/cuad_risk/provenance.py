import hashlib
from pathlib import Path


GENERATOR_ID = "cuad_risk_builder"
TARGET_PROVENANCE = "research_derived_weak_rule"
GENERATOR_SOURCE_FILES = (
    "dataset.py",
    "provenance.py",
    "rollup.py",
    "scoring.py",
    "validation.py",
)


def generator_fingerprint() -> dict[str, object]:
    package_dir = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for filename in GENERATOR_SOURCE_FILES:
        digest.update(filename.encode("utf-8"))
        digest.update(b"\0")
        digest.update((package_dir / filename).read_bytes())
        digest.update(b"\0")
    return {
        "id": GENERATOR_ID,
        "implementation_sha256": digest.hexdigest(),
    }
