import argparse
import json
from dataclasses import dataclass

import torch
from torch.utils.data import Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)


class PairDataset(Dataset):
    def __init__(self, path: str):
        self.items = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line)
                self.items.append(obj)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        x = self.items[idx]
        return x["query"], x["positive"], x["negative"]


@dataclass
class Collator:
    tok: any
    max_length: int = 256

    def __call__(self, batch):
        # превращаем (q, pos, neg) в 2 примера (q,pos)->1 и (q,neg)->0
        q = []
        t = []
        y = []
        for query, pos, neg in batch:
            q.append(query)
            t.append(pos)
            y.append(1)
            q.append(query)
            t.append(neg)
            y.append(0)
        enc = self.tok(q, t, padding=True, truncation=True, max_length=self.max_length, return_tensors="pt")
        enc["labels"] = torch.tensor(y, dtype=torch.long)
        return enc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--base", default="cointegrated/rubert-tiny2")
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--lr", type=float, default=2e-5)
    args = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(args.base)
    model = AutoModelForSequenceClassification.from_pretrained(args.base, num_labels=2)

    ds = PairDataset(args.data)
    split = int(len(ds) * 0.95)
    train_ds = torch.utils.data.Subset(ds, range(0, split))
    eval_ds = torch.utils.data.Subset(ds, range(split, len(ds)))

    ta = TrainingArguments(
        output_dir=args.out,
        per_device_train_batch_size=args.batch,
        per_device_eval_batch_size=args.batch,
        learning_rate=args.lr,
        num_train_epochs=args.epochs,
        eval_strategy="steps",
        eval_steps=200,
        save_strategy="epoch",
        logging_steps=50,
        fp16=torch.cuda.is_available(),
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=ta,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=Collator(tok=tok),
        tokenizer=tok,
    )

    trainer.train()
    trainer.save_model(args.out)
    tok.save_pretrained(args.out)


if __name__ == "__main__":
    main()

