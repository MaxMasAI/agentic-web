"""
services/rag_engine.py - RAG Engine & Multi-Format Document Indexer (PDF, TXT, CSV, JSON, MD, HTML)
"""

import os
import re
import json
import math
from collections import Counter
import pypdf


def extract_text_from_file(file_path: str) -> str:
    """Extracts plain text from various file formats."""
    if not os.path.exists(file_path):
        return ""

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        try:
            reader = pypdf.PdfReader(file_path)
            pages_text = []
            for idx, page in enumerate(reader.pages):
                txt = page.extract_text() or ""
                if txt.strip():
                    pages_text.append(f"[Page {idx+1}]\n{txt}")
            return "\n\n".join(pages_text)
        except Exception as e:
            return f"[Error reading PDF: {e}]"

    elif ext in (".txt", ".md", ".csv", ".json", ".html", ".py", ".log"):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            return f"[Error reading file: {e}]"

    else:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(50000)
        except Exception:
            return "[Binary or unsupported file format]"


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> list:
    """Splits document text into overlapping chunks for semantic retrieval."""
    if not text:
        return []
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_length = 0

    for p in paragraphs:
        p_clean = p.strip()
        if not p_clean:
            continue
        p_len = len(p_clean)

        if current_length + p_len > chunk_size and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = current_chunk[-1:] if overlap > 0 else []
            current_length = len(current_chunk[0]) if current_chunk else 0

        current_chunk.append(p_clean)
        current_length += p_len

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks if chunks else [text[:chunk_size]]


def compute_bm25_score(query_tokens: list, doc_tokens: list, avg_len: float) -> float:
    """Lightweight BM25 keyword relevance score."""
    k1 = 1.5
    b = 0.75
    doc_len = len(doc_tokens)
    if doc_len == 0:
        return 0.0

    doc_counter = Counter(doc_tokens)
    score = 0.0
    for q in query_tokens:
        tf = doc_counter.get(q, 0)
        if tf > 0:
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_len / (avg_len or 1)))
            score += (numerator / denominator)
    return score


def query_indexed_documents(query: str, file_paths: list, top_k: int = 4) -> list:
    """
    Indexes files on the fly and retrieves the top-k most relevant chunks.
    Returns list of dicts: {"file": str, "chunk": str, "score": float}
    """
    if not query or not file_paths:
        return []

    query_tokens = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]
    if not query_tokens:
        query_tokens = query.lower().split()

    all_chunks = []
    total_len = 0

    for fpath in file_paths:
        fname = os.path.basename(fpath)
        raw_text = extract_text_from_file(fpath)
        chunks = chunk_text(raw_text)
        for c in chunks:
            tokens = [w.lower() for w in re.findall(r"\w+", c)]
            total_len += len(tokens)
            all_chunks.append({
                "file": fname,
                "path": fpath,
                "chunk": c,
                "tokens": tokens,
            })

    if not all_chunks:
        return []

    avg_len = total_len / len(all_chunks)

    for item in all_chunks:
        item["score"] = compute_bm25_score(query_tokens, item["tokens"], avg_len)

    all_chunks.sort(key=lambda x: x["score"], reverse=True)
    return all_chunks[:top_k]
