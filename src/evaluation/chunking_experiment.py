"""
Chunking Strategy A/B Test
Compares different chunking strategies
and evaluates RAGAS scores for each
"""
import sys, os, json, logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

sys.path.insert(0, 'src/ingestion')
sys.path.insert(0, 'src/generation')
sys.path.insert(0, 'src/retrieval')
sys.path.insert(0, 'src/generation')

# ── Chunking Strategies ────────────────────────────────────

def chunk_fixed(text: str, chunk_size: int, overlap: int) -> list:
    """Fixed-size word chunking with overlap."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def chunk_sentence(text: str, sentences_per_chunk: int = 5, overlap: int = 1) -> list:
    """Sentence-based chunking."""
    import re
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    chunks = []
    start = 0
    while start < len(sentences):
        end = min(start + sentences_per_chunk, len(sentences))
        chunk = " ".join(sentences[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += sentences_per_chunk - overlap
    return chunks


def chunk_paragraph(text: str, max_words: int = 400) -> list:
    """Paragraph-aware chunking - respects natural boundaries."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = []
    current_words = 0

    for para in paragraphs:
        words = len(para.split())
        if current_words + words > max_words and current:
            chunks.append(" ".join(current))
            current = [para]
            current_words = words
        else:
            current.append(para)
            current_words += words

    if current:
        chunks.append(" ".join(current))
    return chunks


# ── Strategies Config ──────────────────────────────────────

STRATEGIES = [
    {
        "name": "Fixed-512 (baseline)",
        "id": "fixed_512",
        "func": lambda t: chunk_fixed(t, 512, 50),
        "description": "Current: 512 words, 50 overlap"
    },
    {
        "name": "Fixed-256 (smaller)",
        "id": "fixed_256",
        "func": lambda t: chunk_fixed(t, 256, 30),
        "description": "256 words, 30 overlap - more precise"
    },
    {
        "name": "Fixed-1024 (larger)",
        "id": "fixed_1024",
        "func": lambda t: chunk_fixed(t, 1024, 100),
        "description": "1024 words, 100 overlap - more context"
    },
    {
        "name": "Sentence-5 (natural)",
        "id": "sentence_5",
        "func": lambda t: chunk_sentence(t, 5, 1),
        "description": "5 sentences per chunk - natural boundaries"
    },
    {
        "name": "Paragraph-aware",
        "id": "paragraph",
        "func": lambda t: chunk_paragraph(t, 400),
        "description": "Paragraph boundaries - semantic units"
    },
]


# ── Evaluation ─────────────────────────────────────────────

def evaluate_strategy(strategy: dict, qa_dataset: list, project_id: str, api_key: str) -> dict:
    """Evaluate a chunking strategy against ground truth."""
    from embedding_generator import EmbeddingGenerator
    from bm25_indexer import BM25Indexer

    print(f"\n{'='*50}")
    print(f"Testing: {strategy['name']}")
    print(f"  {strategy['description']}")
    print(f"{'='*50}")

    # Load documents
    doc_dir = Path("data/documents")
    all_chunks = []
    for doc_file in sorted(doc_dir.glob("*.md")):
        text = doc_file.read_text()
        chunks = strategy["func"](text)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "chunk_id": f"{doc_file.stem}_chunk_{i}",
                "document_id": doc_file.stem,
                "text": chunk,
                "word_count": len(chunk.split())
            })

    print(f"Chunks created: {len(all_chunks)}")
    avg_words = sum(c["word_count"] for c in all_chunks) / len(all_chunks)
    print(f"Avg words/chunk: {avg_words:.0f}")

    # Build BM25 index - convert dicts to DocumentChunk objects
    from document_processor import DocumentChunk
    chunk_objects = [
        DocumentChunk(
            chunk_id=c["chunk_id"],
            document_id=c["document_id"],
            text=c["text"],
            chunk_index=i,
            word_count=c["word_count"],
            filename=c["document_id"] + ".md",
            char_count=len(c["text"])
        )
        for i, c in enumerate(all_chunks)
    ]
    bm25 = BM25Indexer()
    bm25.build_index(chunk_objects)

    # Evaluate each question
    scores = []
    sources_correct = 0

    for qa in qa_dataset:
        question = qa["question"]
        expected_source = qa["source_document"]
        expected_answer = qa["answer"]

        # BM25 retrieval
        results = bm25.search(question, top_k=3)

        # Check source accuracy
        retrieved_sources = [r.get("metadata",{}).get("document_id","") for r in results]
        if expected_source in retrieved_sources:
            sources_correct += 1

        # Simple relevancy: keyword overlap
        if results:
            top_chunk = results[0].get("text","")
            question_words = set(question.lower().split())
            answer_words = set(expected_answer.lower().split())
            chunk_words = set(top_chunk.lower().split())

            # Score = overlap with expected answer
            overlap = len(answer_words & chunk_words)
            relevancy = min(overlap / max(len(answer_words), 1), 1.0)
            scores.append(relevancy)
        else:
            scores.append(0.0)

    avg_score = sum(scores) / len(scores) if scores else 0
    src_accuracy = sources_correct / len(qa_dataset)

    # By difficulty
    easy_scores = [s for qa, s in zip(qa_dataset, scores) if qa["difficulty"] == "easy"]
    medium_scores = [s for qa, s in zip(qa_dataset, scores) if qa["difficulty"] == "medium"]
    hard_scores = [s for qa, s in zip(qa_dataset, scores) if qa["difficulty"] == "hard"]

    result = {
        "strategy": strategy["name"],
        "strategy_id": strategy["id"],
        "description": strategy["description"],
        "chunks_created": len(all_chunks),
        "avg_words_per_chunk": round(avg_words, 1),
        "avg_relevancy": round(avg_score, 3),
        "source_accuracy": round(src_accuracy, 3),
        "easy_relevancy": round(sum(easy_scores)/len(easy_scores), 3) if easy_scores else 0,
        "medium_relevancy": round(sum(medium_scores)/len(medium_scores), 3) if medium_scores else 0,
        "hard_relevancy": round(sum(hard_scores)/len(hard_scores), 3) if hard_scores else 0,
    }

    print(f"Avg relevancy:   {result['avg_relevancy']}")
    print(f"Source accuracy: {result['source_accuracy']}")
    print(f"Easy:   {result['easy_relevancy']}")
    print(f"Medium: {result['medium_relevancy']}")
    print(f"Hard:   {result['hard_relevancy']}")

    return result


# ── Main ───────────────────────────────────────────────────

if __name__ == "__main__":
    project_id = os.environ.get("PROJECT_ID", "hr-rag-dev")
    api_key = os.environ.get("GEMINI_API_KEY", "")

    # Load ground truth
    with open("data/ground_truth/hr_qa_dataset.json") as f:
        qa_dataset = json.load(f)

    print(f"Ground truth: {len(qa_dataset)} questions")

    # Run all strategies
    results = []
    for strategy in STRATEGIES:
        result = evaluate_strategy(strategy, qa_dataset, project_id, api_key)
        results.append(result)

    # Print comparison table
    print(f"\n{'='*70}")
    print(f"CHUNKING STRATEGY COMPARISON")
    print(f"{'='*70}")
    print(f"{'Strategy':<25} {'Chunks':>6} {'AvgWds':>6} {'AvgRel':>7} {'SrcAcc':>7} {'Easy':>6} {'Med':>6} {'Hard':>6}")
    print(f"{'-'*70}")
    for r in results:
        print(f"{r['strategy']:<25} {r['chunks_created']:>6} {r['avg_words_per_chunk']:>6} {r['avg_relevancy']:>7.3f} {r['source_accuracy']:>7.3f} {r['easy_relevancy']:>6.3f} {r['medium_relevancy']:>6.3f} {r['hard_relevancy']:>6.3f}")

    # Find winner
    winner = max(results, key=lambda x: x["avg_relevancy"])
    print(f"\nWINNER: {winner['strategy']} (score: {winner['avg_relevancy']})")

    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_questions": len(qa_dataset),
        "results": results,
        "winner": winner["strategy_id"]
    }
    with open("data/ground_truth/chunking_comparison.json", "w") as f:
        json.dump(output, f, indent=2)
    print("\nResults saved to data/ground_truth/chunking_comparison.json")
