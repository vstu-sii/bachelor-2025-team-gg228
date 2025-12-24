import argparse
import json

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


def score(model, tok, pairs, max_length=256):
    with torch.no_grad():
        batch = tok(
            [p[0] for p in pairs],
            [p[1] for p in pairs],
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        out = model(**batch).logits
        if out.shape[-1] == 1:
            return torch.sigmoid(out).squeeze(-1).cpu().tolist()
        probs = torch.softmax(out, dim=-1)
        return probs[:, -1].cpu().tolist()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--model", required=True, help="path or HF model id")
    ap.add_argument("--max-length", type=int, default=256)
    ap.add_argument("--limit", type=int, default=2000)
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSequenceClassification.from_pretrained(args.model)
    model.eval()

    wins = 0
    total = 0
    buf = []
    with open(args.data, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            buf.append(obj)
            if len(buf) >= args.limit:
                break

    for obj in buf:
        q = obj["query"]
        pos = obj["positive"]
        neg = obj["negative"]
        sp, sn = score(model, tok, [(q, pos), (q, neg)], max_length=args.max_length)
        wins += 1 if sp > sn else 0
        total += 1

    acc = wins / total if total else 0.0
    print(f"pairwise_accuracy={acc:.4f} ({wins}/{total})")


if __name__ == "__main__":
    main()

