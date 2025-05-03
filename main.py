#!/usr/bin/env python3
"""
main.py

Usage:
    python main.py --text-fileinput.txt

Reads text from input file, analyzes PII with Presidio Analyzer,
then anonymizes it with Presidio Anonymizer and prints the result.
"""

import argparse
import json
import sys
import requests
import os
from presidio_service import analyze_text, anonymize_text, default_anonymizers

# Endpoints for your running Presidio Docker containers
ANALYZER_URL   = 'http://localhost:5002/analyze'
ANONYMIZER_URL = 'http://localhost:5001/anonymize'

def load_text_from_file(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def main():
    parser = argparse.ArgumentParser(description="Analyze & anonymize text via Presidio Docker containers")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--text-file', help="Path to a .txt file containing the text to process")
    group.add_argument('--text-path', help="Path to a directory containing .txt files to process")
    parser.add_argument('--lang',     default='en', help="Language code (ISO_639-1), default 'en'")
    parser.add_argument('--threshold',type=float, default=0.5, help="Minimum detection score, default 0.5")
    parser.add_argument('--quiet', action='store_true', help="Suppress info messages; only output errors and anonymized text")
    args = parser.parse_args()

    anonymizers = default_anonymizers

    # Build list of files to process
    files_to_process = []
    if args.text_file:
        if not os.path.isfile(args.text_file):
            print(f"Error: {args.text_file!r} is not a file", file=sys.stderr)
            sys.exit(1)
        files_to_process = [args.text_file]
    elif args.text_path:
        if not os.path.isdir(args.text_path):
            print(f"Error: {args.text_path!r} is not a directory", file=sys.stderr)
            sys.exit(1)
        files = [f for f in os.listdir(args.text_path) if os.path.isfile(os.path.join(args.text_path, f)) and not f.startswith('.')]
        if not files:
            print(f"No non-hidden files found in {args.text_path!r}", file=sys.stderr)
            sys.exit(1)
        files_to_process = [os.path.join(args.text_path, f) for f in files]

    for fpath in files_to_process:
        fname = os.path.basename(fpath)
        try:
            text = load_text_from_file(fpath)
        except Exception as e:
            print(f"[!] Could not read {fname}: {e}", file=sys.stderr)
            continue
        if not args.quiet:
            print(f"\n[+] Processing file: {fname}")
            print(f"[+] Loaded {len(text)} characters from {fname!r}")
        detections = analyze_text(text, language=args.lang, score_threshold=args.threshold)
        if not args.quiet:
            print(f"[+] Detected {len(detections)} PII entities in {fname}")
            for ent in detections:
                print(f"    - {ent['entity_type']} at [{ent['start']}–{ent['end']}] (score={ent['score']:.2f})")
        result = anonymize_text(text, detections, anonymizers)
        anonymized_text = result.get("text") or result.get("result") or ""
        print(f"=== Anonymized Text ({fname}) ===")
        print(anonymized_text)
        print("================================")

if __name__ == '__main__':
    try:
        main()
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Presidio service: {e}", file=sys.stderr)
        sys.exit(1)
