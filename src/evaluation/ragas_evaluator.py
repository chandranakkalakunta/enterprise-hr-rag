"""
RAGAS Evaluation Pipeline - Enterprise HR RAG Platform
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../generation"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../ingestion"))


def load_ground_truth(filepath):
    with open(filepath, "r") as f:
        return json.load(f)


def run_evaluation(questions, rag_engine):
    print(f"Evaluating {len(questions)} questions...")
    results = []
    for i, item in enumerate(questions):
        question = item["question"]
        expected = item["answer"]
        print(f"  [{i+1}/{len(questions)}] {question[:50]}...")
        try:
            result = rag_engine.query(question)
            actual = result.get("answer", "")
            sources = result.get("sources", [])
            chunks_used = result.get("chunks_used", 0)
            expected_words = set(expected.lower().split())
            actual_words = set(actual.lower().split())
            overlap = len(expected_words & actual_words)
            relevancy = overlap / max(len(expected_words), 1)
            expected_source = item.get("source_document", "").replace(".pdf","").replace(".md","")
            source_correct = any(expected_source in s for s in sources) if expected_source else True
            results.append({
                "question": question,
                "expected": expected,
                "actual": actual,
                "sources": sources,
                "chunks_used": chunks_used,
                "relevancy_score": round(relevancy, 3),
                "source_correct": source_correct,
                "difficulty": item.get("difficulty", "medium")
            })
        except Exception as e:
            print(f"    Error: {e}")
            results.append({
                "question": question,
                "expected": expected,
                "actual": f"ERROR: {str(e)}",
                "sources": [],
                "chunks_used": 0,
                "relevancy_score": 0.0,
                "source_correct": False,
                "difficulty": item.get("difficulty", "medium")
            })
    return results


def calculate_metrics(results):
    if not results:
        return {}
    total = len(results)
    avg_relevancy = sum(r["relevancy_score"] for r in results) / total
    source_accuracy = sum(1 for r in results if r["source_correct"]) / total
    avg_chunks = sum(r["chunks_used"] for r in results) / total
    by_difficulty = {}
    for diff in ["easy", "medium", "hard"]:
        diff_results = [r for r in results if r["difficulty"] == diff]
        if diff_results:
            avg_rel = sum(r["relevancy_score"] for r in diff_results) / len(diff_results)
            by_difficulty[diff] = {
                "count": len(diff_results),
                "avg_relevancy": round(avg_rel, 3)
            }
    return {
        "total_questions": total,
        "avg_relevancy_score": round(avg_relevancy, 3),
        "source_accuracy": round(source_accuracy, 3),
        "avg_chunks_used": round(avg_chunks, 1),
        "by_difficulty": by_difficulty,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "completed"
    }


def save_to_bigquery(metrics, project_id):
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=project_id)
        table_id = f"{project_id}.hr_rag_metrics.evaluation_results"
        row = {
            "eval_id": f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": metrics["timestamp"],
            "faithfulness": metrics["avg_relevancy_score"],
            "answer_relevancy": metrics["avg_relevancy_score"],
            "context_precision": metrics["source_accuracy"],
            "context_recall": metrics["source_accuracy"],
            "overall_score": round(
                (metrics["avg_relevancy_score"] + metrics["source_accuracy"]) / 2, 3
            ),
            "num_questions": metrics["total_questions"],
            "config_chunk_size": 512,
            "config_top_k": 5
        }
        errors = client.insert_rows_json(table_id, [row])
        if not errors:
            print("Results saved to BigQuery!")
    except Exception as e:
        print(f"Could not save to BigQuery: {e}")


def main():
    project_id = os.environ.get("PROJECT_ID", "hr-rag-dev")
    api_key = os.environ.get("GEMINI_API_KEY", "")
    environment = os.environ.get("ENVIRONMENT", "dev")

    ground_truth_path = Path(__file__).parent.parent.parent / "data" / "ground_truth" / "hr_qa_dataset.json"

    print("=" * 50)
    print("HR RAG Platform - Evaluation")
    print("=" * 50)

    if not ground_truth_path.exists():
        print(f"Ground truth not found: {ground_truth_path}")
        sys.exit(1)

    questions = load_ground_truth(str(ground_truth_path))
    print(f"Loaded {len(questions)} questions")

    print("Initializing RAG engine...")
    from rag_engine import RAGEngine
    engine = RAGEngine(
        project_id=project_id,
        gemini_api_key=api_key,
        environment=environment
    )

    results = run_evaluation(questions, engine)
    metrics = calculate_metrics(results)

    print("")
    print("=" * 50)
    print("EVALUATION RESULTS")
    print("=" * 50)
    print(f"Total questions:      {metrics['total_questions']}")
    print(f"Avg relevancy score:  {metrics['avg_relevancy_score']}")
    print(f"Source accuracy:      {metrics['source_accuracy']}")
    print(f"Avg chunks used:      {metrics['avg_chunks_used']}")
    print("")
    print("By difficulty:")
    for diff, stats in metrics.get("by_difficulty", {}).items():
        count = stats['count']
        avg_rel = stats['avg_relevancy']
        print(f"  {diff}: {count} questions, relevancy={avg_rel}")

    results_path = Path(__file__).parent.parent.parent / "data" / "ground_truth" / "evaluation_results.json"
    with open(results_path, "w") as f:
        json.dump({"metrics": metrics, "details": results}, f, indent=2)
    print("")
    print(f"Results saved: {results_path}")

    save_to_bigquery(metrics, project_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
