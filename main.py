#!/usr/bin/env python3
"""
main.py

Usage:
    python main.py input.txt

Reads text from input file, analyzes PII with Presidio Analyzer,
then anonymizes it with Presidio Anonymizer and prints the result.
"""

import argparse
import json
import sys
import requests

# Endpoints for your running Presidio Docker containers
ANALYZER_URL   = 'http://localhost:5002/analyze'
ANONYMIZER_URL = 'http://localhost:5001/anonymize'

def analyze_text(text: str, language: str = 'en', score_threshold: float = 0.5):
    """Call Presidio Analyzer and return the list of detections."""
    payload = {
        "text": text,
        "language": language,
        "score_threshold": score_threshold
    }
    resp = requests.post(ANALYZER_URL, json=payload)
    resp.raise_for_status()
    return resp.json()

def anonymize_text(text: str, analyzer_results: list, anonymizers: dict = None):
    """
    Call Presidio Anonymizer.
    - text: original text
    - analyzer_results: list of dicts with start/end/entity_type/score
    - anonymizers: dict mapping entity_type or 'DEFAULT' to operator configs
    """
    if anonymizers is None:
        # default: replace each entity with "<ENTITY_TYPE>"
        anonymizers = {"DEFAULT": {"type": "replace", "new_value": "<ENTITY>"}}
    payload = {
        "text": text,
        "analyzer_results": analyzer_results,
        "anonymizers": anonymizers
    }
    resp = requests.post(ANONYMIZER_URL, json=payload)
    resp.raise_for_status()
    return resp.json()

def load_text_from_file(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def main():
    parser = argparse.ArgumentParser(description="Analyze & anonymize text via Presidio Docker containers")
    parser.add_argument('input_file', help="Path to the .txt file containing the text to process")
    parser.add_argument('--lang',     default='en', help="Language code (ISO_639-1), default 'en'")
    parser.add_argument('--threshold',type=float, default=0.5, help="Minimum detection score, default 0.5")
    args = parser.parse_args()

    text = load_text_from_file(args.input_file)
    print(f"[+] Loaded {len(text)} characters from {args.input_file!r}")

    # 1) Analyze
    print("[+] Sending to Presidio Analyzer...")
    detections = analyze_text(text, language=args.lang, score_threshold=args.threshold)
    print(f"[+] Detected {len(detections)} PII entities:")
    for ent in detections:
        print(f"    - {ent['entity_type']} at [{ent['start']}–{ent['end']}] (score={ent['score']:.2f})")

    # 2) Configure your anonymizers here:
    anonymizers = {
        "DEFAULT":      { "type": "replace", "new_value": "ANONYMIZED" },
        "PHONE_NUMBER": { "type": "mask",    "masking_char": "*", "chars_to_mask": 4, "from_end": True },
        # e.g. email: redact entirely
        "EMAIL_ADDRESS": { "type": "redact" }
    }

    # 3) Anonymize
    print("[+] Sending to Presidio Anonymizer...")
    result = anonymize_text(text, detections, anonymizers)
    anonymized_text = result.get("text") or result.get("result") or ""
    
    print("\n=== Anonymized Text ===")
    print(anonymized_text)
    print("========================")

if __name__ == '__main__':
    try:
        main()
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Presidio service: {e}", file=sys.stderr)
        sys.exit(1)

