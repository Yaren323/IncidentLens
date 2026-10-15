"""Local ticket classifier: scoped ML + category ML + limited input checks.

Model artifacts are trusted local build outputs, never uploaded by end users.
"""
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import joblib
from app.services.knowledge import CATEGORY_GUIDES

MODEL_PATH=Path(__file__).resolve().parents[2]/'models'/'incidentlens_models.joblib'
URL=re.compile(r'(?:https?://)?(?:www\.)?([a-z0-9-]+(?:\.[a-z0-9-]+)+)',re.IGNORECASE)
INSTRUCTION_ATTACK=re.compile(r'(ignore (all|previous) instructions|önceki talimatları (yok say|unut)|system prompt|developer message|sistem promptunu göster|api anahtarını ver|şifreni söyle)',re.IGNORECASE)
# Explicitly disallow secret disclosure and instruction redirection; ML is not a security boundary.
@dataclass(frozen=True)
class Prediction:
    category:str
    confidence:float
    target:str

@lru_cache(maxsize=1)
def models():
    if not MODEL_PATH.exists():
        raise RuntimeError('Model bulunamadı. python scripts/train_model.py çalıştırılmalı.')
    return joblib.load(MODEL_PATH)

def predict(text:str)->Prediction|None:
    text=' '.join(text.strip().split())
    if len(text)<12 or len(text)>500 or INSTRUCTION_ATTACK.search(text):
        return None
    pair=models()
    scope=pair['scope']
    scope_proba=scope.predict_proba([text])[0]
    scope_prob=float(scope_proba[list(scope.classes_).index('it')])
    if scope_prob<0.58:
        return None
    cat=pair['category']
    probs=cat.predict_proba([text])[0]
    best=int(probs.argmax())
    category=str(cat.classes_[best])
    confidence=float(probs[best])
    # A very low score means 'uncertain', not 'not an IT problem'.
    if confidence<0.20 or category not in CATEGORY_GUIDES:
        return None
    match=URL.search(text)
    return Prediction(category,confidence,match.group(1).lower() if match else '')
