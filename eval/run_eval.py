import json
from pathlib import Path

import requests


API_URL = "http://127.0.0.1:8000/ask"


def detect_sentiment(answer: str) -> str:
    text = answer.lower().strip()

    red_patterns = [
        "sentiment: red",
        "**sentiment: red**",
        "customer sentiment: red",
        "sentiment is red",
    ]
    yellow_patterns = [
        "sentiment: yellow",
        "**sentiment: yellow**",
        "customer sentiment: yellow",
        "sentiment is yellow",
    ]
    green_patterns = [
        "sentiment: green",
        "**sentiment: green**",
        "customer sentiment: green",
        "sentiment is green",
    ]

    if any(p in text for p in red_patterns):
        return "Red"
    if any(p in text for p in yellow_patterns):
        return "Yellow"
    if any(p in text for p in green_patterns):
        return "Green"

    return "Unknown"


def keyword_hits(answer: str, keywords: list[str]) -> int:
    text = answer.lower()
    return sum(1 for kw in keywords if kw.lower() in text)


def main():
    dataset_path = Path("eval/synthetic_eval_set.json")
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))

    results = []
    correct_sentiment = 0
    total_keyword_hits = 0
    total_keywords = 0

    for item in dataset:
        payload = {
            "question": item["question"],
            "customer_id": item["customer_id"],
        }

        response = requests.post(API_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        answer = data.get("answer", "")
        predicted_sentiment = detect_sentiment(answer)
        expected_sentiment = item["expected_sentiment"]

        sentiment_correct = predicted_sentiment == expected_sentiment
        if sentiment_correct:
            correct_sentiment += 1

        hits = keyword_hits(answer, item["expected_keywords"])
        total_keyword_hits += hits
        total_keywords += len(item["expected_keywords"])

        results.append({
            "id": item["id"],
            "question": item["question"],
            "customer_id": item["customer_id"],
            "expected_sentiment": expected_sentiment,
            "predicted_sentiment": predicted_sentiment,
            "sentiment_correct": sentiment_correct,
            "keyword_hits": hits,
            "keyword_total": len(item["expected_keywords"]),
            "answer": answer,
        })

    sentiment_accuracy = correct_sentiment / len(dataset)
    keyword_recall = total_keyword_hits / total_keywords if total_keywords else 0.0

    summary = {
        "num_cases": len(dataset),
        "sentiment_accuracy": round(sentiment_accuracy, 3),
        "keyword_recall": round(keyword_recall, 3),
        "results": results,
    }

    out_path = Path("eval/eval_results.json")
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Evaluation complete")
    print(json.dumps({
        "num_cases": summary["num_cases"],
        "sentiment_accuracy": summary["sentiment_accuracy"],
        "keyword_recall": summary["keyword_recall"],
        "results_file": str(out_path),
    }, indent=2))


if __name__ == "__main__":
    main()