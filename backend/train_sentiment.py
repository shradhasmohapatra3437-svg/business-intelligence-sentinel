import argparse
import os
import torch
import numpy as np
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)

def compute_metrics(eval_pred):
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="weighted"
    )
    acc = accuracy_score(labels, predictions)
    return {"accuracy": acc, "f1": f1, "precision": precision, "recall": recall}

def train_document_level(args):
    print("\n" + "="*50)
    print("STAGE 1: Fine-tuning DistilBERT for Document-Level Sentiment")
    print("="*50)
    
    try:
        dataset = load_dataset("financial_phrasebank", "sentences_allagree")
    except Exception as e:
        print(f"Error loading dataset: {e}. Ensure you have internet access.")
        return

    train_val_split = dataset["train"].train_test_split(test_size=0.2, seed=42)
    train_dataset = train_val_split["train"]
    val_dataset = train_val_split["test"]
    
    if args.limit_data > 0:
        train_dataset = train_dataset.select(range(min(args.limit_data, len(train_dataset))))
        val_dataset = val_dataset.select(range(min(int(args.limit_data * 0.2) + 1, len(val_dataset))))

    model_name = "distilbert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=3)
    
    def tokenize_function(examples):
        return tokenizer(examples["sentence"], padding="max_length", truncation=True, max_length=128)
    
    tokenized_train = train_dataset.map(tokenize_function, batched=True)
    tokenized_val = val_dataset.map(tokenize_function, batched=True)
    
    out_dir = os.path.join(args.output_dir, "distilbert-financial-sentiment")
    
    training_args = TrainingArguments(
        output_dir=out_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        use_cpu=not torch.cuda.is_available(),
        report_to="none"
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        compute_metrics=compute_metrics,
    )
    
    print("Starting DistilBERT fine-tuning...")
    trainer.train()
    
    print("Evaluating...")
    eval_results = trainer.evaluate()
    for key, value in eval_results.items():
        if key.startswith("eval_"):
            print(f"{key[5:].capitalize()}: {value:.4f}")
            
    print(f"Saving to '{out_dir}'...")
    model.save_pretrained(out_dir)
    tokenizer.save_pretrained(out_dir)

def train_absa(args):
    print("\n" + "="*50)
    print("STAGE 2: Fine-tuning DeBERTa for Aspect-Based Sentiment Analysis")
    print("="*50)
    
    print("Loading SemEval 2014 Task 4 dataset...")
    try:
        # Note: we use laptop reviews as a proxy since financial ABSA datasets are rarely public
        dataset = load_dataset("jakartaresearch/semeval-absa", "laptop")
    except Exception as e:
        print(f"Error loading dataset: {e}. Ensure you have internet access.")
        return

    # Filter out neutral/conflict labels for simplicity (keep positive/negative)
    def filter_labels(example):
        return example['polarity'] in [0, 1, 2] # 0=negative, 1=neutral, 2=positive

    train_dataset = dataset["train"].filter(filter_labels)
    val_dataset = dataset["validation"].filter(filter_labels)
    
    if args.limit_data > 0:
        train_dataset = train_dataset.select(range(min(args.limit_data, len(train_dataset))))
        val_dataset = val_dataset.select(range(min(int(args.limit_data * 0.2) + 1, len(val_dataset))))

    model_name = "microsoft/deberta-v3-base"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=3)
    
    def tokenize_absa(examples):
        # Format: "[CLS] sentence [SEP] aspect [SEP]"
        return tokenizer(
            text=examples["text"],
            text_pair=examples["term"],
            padding="max_length",
            truncation=True,
            max_length=128
        )
    
    tokenized_train = train_dataset.map(tokenize_absa, batched=True)
    tokenized_val = val_dataset.map(tokenize_absa, batched=True)
    
    # Rename polarity to label
    tokenized_train = tokenized_train.rename_column("polarity", "label")
    tokenized_val = tokenized_val.rename_column("polarity", "label")
    
    out_dir = os.path.join(args.output_dir, "deberta-financial-absa")
    
    training_args = TrainingArguments(
        output_dir=out_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        use_cpu=not torch.cuda.is_available(),
        report_to="none"
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        compute_metrics=compute_metrics,
    )
    
    print("Starting DeBERTa ABSA fine-tuning...")
    trainer.train()
    
    print("Evaluating...")
    eval_results = trainer.evaluate()
    for key, value in eval_results.items():
        if key.startswith("eval_"):
            print(f"{key[5:].capitalize()}: {value:.4f}")
            
    print(f"Saving to '{out_dir}'...")
    model.save_pretrained(out_dir)
    tokenizer.save_pretrained(out_dir)

def main():
    parser = argparse.ArgumentParser(description="Train stock news sentiment models")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--limit_data", type=int, default=0, help="For fast testing")
    parser.add_argument("--output_dir", type=str, default="./models")
    parser.add_argument("--stage", type=str, default="both", choices=["1", "2", "both"])
    
    args = parser.parse_args()
    
    if args.stage in ["1", "both"]:
        train_document_level(args)
        
    if args.stage in ["2", "both"]:
        train_absa(args)
        
    print("\nAll requested training stages completed successfully!")

if __name__ == "__main__":
    main()
