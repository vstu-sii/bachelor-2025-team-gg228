from __future__ import annotations

from functools import lru_cache
from typing import Iterable

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.config import settings


@lru_cache(maxsize=1)
def get_tokenizer():
    name_or_path = str(settings.model_path) if settings.model_path else settings.base_model
    return AutoTokenizer.from_pretrained(name_or_path)


@lru_cache(maxsize=1)
def get_model():
    name_or_path = str(settings.model_path) if settings.model_path else settings.base_model
    model = AutoModelForSequenceClassification.from_pretrained(name_or_path)
    model.eval()
    return model


def score_pairs(pairs: list[tuple[str, str]]) -> list[float]:
    tok = get_tokenizer()
    model = get_model()

    with torch.no_grad():
        batch = tok(
            [p[0] for p in pairs],
            [p[1] for p in pairs],
            padding=True,
            truncation=True,
            max_length=settings.max_length,
            return_tensors="pt",
        )
        out = model(**batch)
        logits = out.logits

        if logits.shape[-1] == 1:
            probs = torch.sigmoid(logits).squeeze(-1)
            return probs.cpu().tolist()

        probs = torch.softmax(logits, dim=-1)
        # берём вероятность класса "релевантно" = последний класс
        return probs[:, -1].cpu().tolist()

