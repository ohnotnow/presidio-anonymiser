import requests
import os

ANALYZER_URL   = os.getenv('ANALYZER_URL', 'http://localhost:5002/analyze')  # noqa: E501
ANONYMIZER_URL = os.getenv('ANONYMIZER_URL', 'http://localhost:5001/anonymize')  # noqa: E501

default_anonymizers = {
    "DEFAULT":      { "type": "replace", "new_value": "ANONYMIZED" },
    "PHONE_NUMBER": { "type": "mask",    "masking_char": "*", "chars_to_mask": 4, "from_end": True },
    "EMAIL_ADDRESS": { "type": "redact" }
}

def analyze_text(text: str, language: str = 'en', score_threshold: float = 0.5):
    payload = {
        "text": text,
        "language": language,
        "score_threshold": score_threshold
    }
    resp = requests.post(ANALYZER_URL, json=payload)
    resp.raise_for_status()
    return resp.json()

def anonymize_text(text: str, analyzer_results: list, anonymizers: dict|None = None):
    if anonymizers is None:
        anonymizers = {"DEFAULT": {"type": "replace", "new_value": "<ENTITY>"}}
    payload = {
        "text": text,
        "analyzer_results": analyzer_results,
        "anonymizers": anonymizers
    }
    resp = requests.post(ANONYMIZER_URL, json=payload)
    resp.raise_for_status()
    return resp.json()
