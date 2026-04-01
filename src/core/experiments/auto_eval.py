
"""
Automated Thesis Evaluation Engine
----------------------------------
A robust, scalable pipeline for evaluating search retrieval performance.
Features:
- Dual Modes: 'ai' (LLM Judge) vs 'data' (Raw Metrics Dump).
- Rich Telemetry: Captures Hybrid, Semantic, BM25 scores, and Latency.
- Scalable: Built to handle 50+ queries robustly.
- Evaluation: Computes Relevance using AI or Ground Truth logic.

Usage:
    python src/core/experiments/auto_eval.py --mode ai --queries 50
    python src/core/experiments/auto_eval.py --mode data
"""

import sys
import requests
import os
import csv
import time
import json
import logging
import argparse
import random
from datetime import datetime
from typing import List, Dict, Any

# Ensure correct path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Import Search Logic
# Note: we bind to 'core' because we appended src/ folder to path
# Import Search Logic
# Note: we bind to 'core' because we appended src/ folder to path
from core.db.operations.search_flask.hybrid_search import search_hybrid
from core.db.operations.search_flask.rrf_search import search_rrf
from core.db.operations.search_queries import execute_vector_query, execute_bm25_query  # <-- Added
from core.db.db_connection import db_connection
from core.models.ai_model import get_embedder
from ai.OllamaClient import OllamaClient

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("thesis_eval_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ThesisEval")

# --- Configuration ---
DEFAULT_QUERIES = [
    # --- Original 10 ---
    "What is AI engineering?",
    "How does RRF work?",
    "Explain hybrid search fusion strategies.",
    "Difference between semantic and keyword search.",
    "What is the architecture of a transformer?",
    "How to optimize PostgreSQL for vector search?",
    "Limitations of BM25 algorithm.",
    "Benefits of Retrieval Augmented Generation.",
    "Explain the concept of embeddings.",
    "How does sparse vs dense retrieval differ?",
    "What are the challenges of long-context LLMs?",
    "Explain Chain-of-Thought prompting.",
    "How does Reinforcement Learning from Human Feedback (RLHF) work?",
    "What is the vanishing gradient problem?",
    "Compare BERT and GPT architectures.",
    "How do diffusion models generate images?",
    "What is contrastive learning?",
    "Explain the attention mechanism in deep learning.",
    "What are Hallucinations in LLMs?",
    "How does quantization reduce model size?",
    "What is LoRA (Low-Rank Adaptation)?",
    "Explain Zero-shot vs Few-shot learning.",
    "What is the role of a vector index like HNSW?",
    "Advantages of Reciprocal Rank Fusion over linear combination.",
    "What is multi-modal learning?",
    "Explain the bias-variance tradeoff.",
    "What are Graph Neural Networks?",
    "How does self-supervised learning work?",
    "What is catastrophic forgetting in neural networks?",
    "Explain the differences between L1 and L2 regularization.",
    "What is prompt reliability?",
    "How does temperature affect LLM sampling?",
    "What are mixture-of-experts (MoE) models?",
    "How to evaluate RAG systems?",
    "What is dense passage retrieval?",
    "Explain the concept of tokenization in NLP.",
    "What are adversarial attacks in AI?",
    "How does Federated Learning preserve privacy?",
    "What is the purpose of positional encodings in Transformers?",
    "Explain the difference between encoder-only and decoder-only models.",
    "What is curriculum learning?",
    "How do vision transformers (ViT) differ from CNNs?",
    "What is active learning?",
    "Explain the role of hyperparameters in model training.",
    "What is data augmentation?",
    "How does transfer learning benefit NLP tasks?",
    "What is a knowledge graph?",
    "Explain the concept of latent space.",
    "What are the ethical concerns of generative AI?",
    "How does beam search decoding work?"
]

STRATEGIES = [
    {"name": "hybrid_linear", "func": "hybrid", "params": {"fusion_strategy": "linear"}},
    {"name": "rrf", "func": "rrf"},
    {"name": "semantic_only", "func": "semantic"},
    {"name": "keyword_refined", "func": "keyword"}
]

# --- Metric Extraction ---
def extract_metrics(doc_tuple: tuple, stats: Dict, strategy_type: str) -> Dict:
    """
    Extracts rich technical scores from a result tuple and stats dictionary.
    Tuple typically: (doc_id, score, content, ...)
    """
    try:
        doc_id = doc_tuple[0]
        content = doc_tuple[1]
        score = doc_tuple[2]
        
        sem_score = 0
        bm25_score = 0
        
        if strategy_type == 'hybrid' and 'components' in stats:
            comp = stats['components'].get(doc_id, {})
            sem_score = comp.get('sem_score', 0)
            bm25_score = comp.get('bm25_score', 0)
            
        return {
            "doc_id": doc_id,
            "hybrid_score": round(float(score), 4),
            "semantic_score": round(float(sem_score), 4),
            "bm25_score": round(float(bm25_score), 4),
            "response": str(content)[:60].replace('\n', ' ') + "..."
        }
    except IndexError:
        return {"doc_id": "Error", "response": "Tuple Unpack Error"}

# --- AI Judge ---
def judge_relevance(query: str, content: str) -> Dict[str, Any]:
    """
    Evaluates relevance of content to query using standardized OllamaClient.
    """
    if not content:
        return {"is_relevant": False, "score": 0, "reason": "Empty Content"}

    # Initialize client from environment or defaults
    model_name = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")
    client = OllamaClient(model=model_name)
    
    prompt = (
        f"Query: {query}\n"
        f"Content fragment: {content[:800]}\n\n"
        "Task: Evaluate if the content matches the query.\n"
        "Return strictly JSON: {\"is_relevant\": <bool>, \"score\": <0-10>, \"reason\": \"<short text>\"}"
    )
    
    try:
        # Use standardized client with JSON format requirement
        # Note: we use generate_response but add the format logic if needed.
        # However, OllamaClient.py uses /api/generate without format: json by default.
        # We'll just use the raw response and parse it as we did before.
        
        response_text = client.generate_response(
            prompt=prompt,
            system_instruction="You are a meticulous Evaluation AI that outputs ONLY JSON.",
            temperature=0
        )
        
        clean_text = response_text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].strip()
        
        try:
            data = json.loads(clean_text)
            return {
                "is_relevant": data.get("is_relevant", False),
                "score": data.get("score", 0),
                "reason": data.get("reason", "Auto-judged")
            }
        except json.JSONDecodeError:
             return {"is_relevant": False, "score": 0, "reason": "JSON Parse error"}
             
    except Exception as e:
        logger.error(f"Judge Exception: {e}")
        
    return {"is_relevant": False, "score": 0, "reason": "Execution Error"}

# --- Main Engine ---
def run_evaluation(mode: str, query_limit: int):
    logger.info(f"Starting Thesis Evaluation Engine | Mode: {mode.upper()} | Limit: {query_limit} queries")
    
    model = get_embedder("paraphrase-multilingual-MiniLM-L12-v2")
    conn = db_connection()
    if not conn:
        logger.critical("DB Connection Failed!")
        return
    cursor = conn.cursor()

    results_data = []
    queries = DEFAULT_QUERIES[:query_limit]
    
    try:
        for q_idx, query in enumerate(queries):
            logger.info(f"Processing Query {q_idx+1}/{len(queries)}: '{query}'")
            
            query_results = {}  # Aggregator for this query
            
            for strat in STRATEGIES:
                s_name = strat["name"]
                start_ts = time.time()
                docs = []
                stats = {}
                
                try:
                    if strat["func"] == "hybrid":
                        docs, stats = search_hybrid(
                            query=query, conn=conn, cursor=cursor, model=model, 
                            top_k=5, **strat["params"]
                        )
                    elif strat["func"] == "rrf":
                        res = search_rrf(query=query, conn=conn, cursor=cursor, model=model, top_k=5)
                        if isinstance(res, tuple) and len(res) == 2:
                            docs, stats = res
                        else:
                            docs = res
                    elif strat["func"] == "semantic":
                        docs = execute_vector_query(query, conn, cursor, model, top_k=5, threshold=0.0)
                    elif strat["func"] == "keyword":
                        docs = execute_bm25_query(query, cursor, top_k=5)
                            
                except Exception as e:
                    logger.error(f"Search Error ({s_name}): {e}")
                    continue
                
                latency = (time.time() - start_ts) * 1000
                
                # AGGREGATE RESULTS (Pivot by DocID to avoid duplicates)
                for rank, doc_tuple in enumerate(docs):
                    metrics = extract_metrics(doc_tuple, stats, strat["func"])
                    did = metrics["doc_id"]
                    
                    if did not in query_results:
                        query_results[did] = {
                            "timestamp": datetime.now().isoformat(),
                            "query": query,
                            "doc_id": did,
                            "content_preview": metrics["response"],
                            "full_content": doc_tuple[1],
                            "strategies": {}
                        }
                    
                    # Store Strategy-Specific Metrics
                    query_results[did]["strategies"][s_name] = {
                        "rank": rank + 1,
                        "score": metrics["hybrid_score"], # Primary score for that strategy
                        "latency": round(latency, 2)
                    }

            # --- PROCESS AGGREGATED RESULTS FOR THIS QUERY ---
            for did, data in query_results.items():
                row = {
                    "timestamp": data["timestamp"],
                    "query": data["query"],
                    "doc_id": did,
                    "content_preview": data["content_preview"]
                }
                
                # Flatten Strategies
                for strat in STRATEGIES:
                    s = strat["name"]
                    if s in data["strategies"]:
                        info = data["strategies"][s]
                        row[f"{s}_rank"] = info["rank"]
                        row[f"{s}_score"] = info["score"]
                        row[f"{s}_latency"] = info["latency"]
                    else:
                        row[f"{s}_rank"] = "N/A"
                        row[f"{s}_score"] = 0
                        row[f"{s}_latency"] = 0

                # AI Judge (Run ONCE per unique doc)
                if mode == 'ai':
                    judgment = judge_relevance(query, data["full_content"])
                    row["ai_relevant"] = judgment["is_relevant"]
                    row["ai_score"] = judgment["score"]
                    row["ai_reason"] = judgment["reason"]
                    
                    mark = "✅" if row["ai_relevant"] else "❌"
                    print(f"   [AI Judge] Doc: {did} | Score: {row['ai_score']} {mark}")
                else:
                    row["ai_relevant"] = "N/A"
                    row["ai_score"] = "N/A"
                    row["ai_reason"] = "N/A"
                
                results_data.append(row)

    except KeyboardInterrupt:
        logger.warning("Interrupted by user. Saving partial results...")

    # Save to CSV
    filename = f"thesis_results_{mode}_{int(time.time())}.csv"
    if results_data:
        keys = results_data[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results_data)
        logger.info(f"✅ Saved {len(results_data)} rows to {filename}")
    else:
        logger.warning("No results to save.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=['ai', 'data'], default='data', help="Evaluation mode")
    parser.add_argument("--limit", type=int, default=5, help="Number of queries to run")
    args = parser.parse_args()
    
    run_evaluation(args.mode, args.limit)

