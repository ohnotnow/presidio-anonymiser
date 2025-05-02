from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import requests
import os
from presidio_service import analyze_text, anonymize_text, default_anonymizers

ANALYZER_URL   = 'http://localhost:5002/analyze'
ANONYMIZER_URL = 'http://localhost:5001/anonymize'

app = FastAPI(title="Presidio Anonymizer API")

class AnonymizeRequest(BaseModel):
    contents: str
    filename: Optional[str] = None
    lang: Optional[str] = 'en'
    threshold: Optional[float] = 0.5

class Entity(BaseModel):
    start: int
    end: int
    entity_type: str
    score: float

class AnonymizeResponse(BaseModel):
    filename: Optional[str]
    entities: List[Entity]
    anonymized_text: str

def analyze_text(text: str, language: str = 'en', score_threshold: float = 0.5):
    payload = {
        "text": text,
        "language": language,
        "score_threshold": score_threshold
    }
    resp = requests.post(ANALYZER_URL, json=payload)
    resp.raise_for_status()
    return resp.json()

def anonymize_text(text: str, analyzer_results: list, anonymizers: dict = None):
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

@app.post("/anonymize", response_model=AnonymizeResponse)
def anonymize(request: AnonymizeRequest):
    text = request.contents
    filename = request.filename
    lang = request.lang or 'en'
    threshold = request.threshold if request.threshold is not None else 0.5
    try:
        detections = analyze_text(text, language=lang, score_threshold=threshold)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Error communicating with Presidio Analyzer: {e}")
    try:
        result = anonymize_text(text, detections, default_anonymizers)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Error communicating with Presidio Anonymizer: {e}")
    anonymized_text = result.get("text") or result.get("result") or ""
    # Convert detections to Entity models
    entities = [Entity(**{
        "start": ent["start"],
        "end": ent["end"],
        "entity_type": ent["entity_type"],
        "score": ent["score"]
    }) for ent in detections]
    return AnonymizeResponse(
        filename=filename,
        entities=entities,
        anonymized_text=anonymized_text
    )
