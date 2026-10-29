from services.investigation import run_evidence_collection


def run_investigation(context: str | None = None):
    return run_evidence_collection(context)
