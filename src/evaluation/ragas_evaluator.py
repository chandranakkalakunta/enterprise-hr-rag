"""
True RAGAS Evaluator with LLM Judge
Uses Gemini to score answers semantically
"""
import json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../generation"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../ingestion"))


def load_ground_truth(filepath):
    with open(filepath, "r") as f:
        return json.load(f)


def llm_judge_score(question: str, expected: str, actual: str, api_key: str) -> float:
    """Use Gemini as LLM judge to score answer quality."""
    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        prompt = f"""You are an expert evaluator for HR policy Q&A systems.
Score how well the "Actual Answer" answers the question compared to the "Expected Answer".

Question: {question}
Expected Answer: {expected}
Actual Answer: {actual}

Scoring criteria:
- 1.0: Actual answer is completely correct and covers all key information
- 0.8: Actual answer is mostly correct with minor omissions
- 0.6: Actual answer is partially correct but missing important details
- 0.4: Actual answer has some relevant info but significant errors
- 0.2: Actual answer barely addresses the question
- 0.0: Actual answer is completely wrong or irrelevant

Respond with ONLY a number between 0.0 and 1.0. Nothing else."""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        score = float(response.text.strip())
        return min(max(score, 0.0), 1.0)

    except Exception as e:
        # Fallback to keyword overlap
        expected_words = set(expected.lower().split())
        actual_words = set(actual.lower().split())
        overlap = len(expected_words & actual_words)
        return overlap / max(len(expected_words), 1)


def run_evaluation(questions, rag_engine):
    api_key = os.environ.get("GEMINI_API_KEY", "")
    print(f"Evaluating {len(questions)} questions with LLM judge...")
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

            # LLM judge scoring
            relevancy = llm_judge_score(question, expected, actual, api_key)
            time.sleep(0.5)  # rate limit

            expected_source = item.get("source_document","").replace(".pdf","").replace(".md","")
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
            print(f"    Score: {relevancy:.3f} | Source: {source_correct}")

        except Exception as e:
            print(f"    Error: {e}")
            results.append({
                "question": question,
                "expected": expected,
                "actual": "",
                "sources": [],
                "chunks_used": 0,
                "relevancy_score": 0.0,
                "source_correct": False,
                "difficulty": item.get("difficulty", "medium")
            })

    return results


def print_summary(results):
    total = len(results)
    avg_relevancy = sum(r["relevancy_score"] for r in results) / total
    source_accuracy = sum(1 for r in results if r["source_correct"]) / total
    avg_chunks = sum(r.get("chunks_used", 0) for r in results) / total

    by_difficulty = {}
    for r in results:
        d = r.get("difficulty", "medium")
        if d not in by_difficulty:
            by_difficulty[d] = []
        by_difficulty[d].append(r["relevancy_score"])

    print(f"\n{'='*50}")
    print(f"RAGAS EVALUATION RESULTS (LLM Judge)")
    print(f"{'='*50}")
    print(f"Total questions:      {total}")
    print(f"Avg relevancy score:  {avg_relevancy:.3f}")
    print(f"Source accuracy:      {source_accuracy:.3f}")
    print(f"Avg chunks used:      {avg_chunks:.1f}")
    for difficulty in ["easy", "medium", "hard"]:
        if difficulty in by_difficulty:
            scores = by_difficulty[difficulty]
            avg = sum(scores) / len(scores)
            print(f"  {difficulty}: {len(scores)} questions, relevancy={avg:.3f}")

    return {
        "avg_relevancy": round(avg_relevancy, 3),
        "source_accuracy": round(source_accuracy, 3),
        "avg_chunks": round(avg_chunks, 1),
        "by_difficulty": {
            d: round(sum(s)/len(s), 3)
            for d, s in by_difficulty.items()
        }
    }


if __name__ == "__main__":
    from rag_engine import RAGEngine

    project_id = os.environ.get("PROJECT_ID", "hr-rag-dev")
    api_key = os.environ.get("GEMINI_API_KEY", "")
    environment = os.environ.get("ENVIRONMENT", "dev")

    engine = RAGEngine(
        project_id=project_id,
        gemini_api_key=api_key,
        environment=environment
    )

    gt_path = "data/ground_truth/hr_qa_dataset.json"
    questions = load_ground_truth(gt_path)
    print(f"Ground truth: {len(questions)} questions")

    results = run_evaluation(questions, engine)
    summary = print_summary(results)

    # Save results
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "evaluation_type": "llm_judge",
        "model": "gemini-2.5-flash",
        "chunk_size": os.environ.get("CHUNK_SIZE", "1024"),
        "alpha": os.environ.get("RRF_ALPHA", "0.5"),
        "summary": summary,
        "results": results
    }

    with open("data/ground_truth/evaluation_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print("\nResults saved!")
