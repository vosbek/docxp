# DocXP Local-First Strategy — Unified Plan & Retrieval Snippets  
**Stack:** OpenSearch + MinIO (local), Bedrock-only models, Podman → Kubernetes  
**Owner:** Matt / DocXP  
**Date:** 2025-08-16

---

## TL;DR

We’re shipping a **local-first, cloud-optional** DocXP:

- **Runtime:** Podman locally, Kubernetes later (not an AWS-hosted web app).
- **Models:** **Bedrock mandatory** (no local LLMs). Titan for embeddings, Claude for generation.
- **Queue:** Redis + RQ (adapter pattern; can swap to SQS later).
- **Storage:** MinIO (S3-compatible) with a thin adapter (flip to S3 later).
- **Search:** **OpenSearch** single-node with **BM25 + k-NN** hybrid; app-side **RRF** fusion.
- **Citations everywhere:** `path`, `start`, `end`, `commit`, `tool`, `model`.
- **Scope v1:** REST + SSE; GraphQL/WebSockets later.

---

## Required OpenSearch Mapping (correct & portable)

> Set the embedding dimension from your Bedrock Titan embed model at startup (`OPENSEARCH_EMBED_DIM`). Do **not** hardcode.

```json
PUT /docxp_chunks
{
  "settings": { "index.knn": true },
  "mappings": {
    "properties": {
      "content":   { "type": "text" },
      "embedding": { "type": "knn_vector", "dimension": OPENSEARCH_EMBED_DIM },
      "path":      { "type": "keyword" },
      "repo_id":   { "type": "keyword" },
      "commit":    { "type": "keyword" },
      "lang":      { "type": "keyword" },
      "kind":      { "type": "keyword" },
      "start":     { "type": "integer" },
      "end":       { "type": "integer" }
    }
  }
}
```

> *(Optional later)* Add a custom analyzer using `word_delimiter_graph` to split CamelCase/snake_case once v1 is stable.

---

## Hybrid Retrieval — App-Side RRF (ship this)

### A) RRF merge (Python)

```python
from typing import List, Dict, Tuple

def rrf_fuse(
    bm25_hits: List[Dict],
    knn_hits: List[Dict],
    k: int = 60,
    w_bm25: float = 1.2,   # slight bias toward exact tokens/symbols
    w_knn: float = 1.0,
    top_n: int = 10
) -> List[Dict]:
    """Fuse two ranked lists (BM25 & kNN) using Reciprocal Rank Fusion."""
    def to_rank_map(hits: List[Dict]) -> Dict[str, int]:
        return {h["_id"]: i + 1 for i, h in enumerate(hits)}

    bm25_rank = to_rank_map(bm25_hits)
    knn_rank  = to_rank_map(knn_hits)

    ids = set(bm25_rank) | set(knn_rank)
    fused: List[Tuple[str, float]] = []

    for _id in ids:
        score = 0.0
        if _id in bm25_rank:
            score += w_bm25 / (k + bm25_rank[_id])
        if _id in knn_rank:
            score += w_knn / (k + knn_rank[_id])
        fused.append((_id, score))

    fused.sort(key=lambda t: t[1], reverse=True)

    bm25_map = {h["_id"]: h for h in bm25_hits}
    knn_map  = {h["_id"]: h for h in knn_hits}

    merged = []
    for _id, fscore in fused[:top_n]:
        doc = bm25_map.get(_id, knn_map[_id]).copy()
        doc["rrf_score"] = fscore
        src = doc.get("_source", {})
        doc["citation"] = {
            "path":   src.get("path"),
            "start":  src.get("start"),
            "end":    src.get("end"),
            "commit": src.get("commit"),
        }
        merged.append(doc)
    return merged
```

### B) Two-call hybrid with repo/commit filters (Python)

```python
def hybrid_search(os_client, index, query_text, query_vec, repo_id, commit, top_n=10):
    # 1) BM25 (text)
    bm25_body = {
        "size": max(50, top_n * 5),
        "query": {
            "bool": {
                "must": { "multi_match": { "query": query_text, "fields": ["content"], "type": "best_fields" } },
                "filter": [
                    {"term": {"repo_id": repo_id}},
                    {"term": {"commit": commit}}
                ]
            }
        }
    }
    bm25 = os_client.search(index=index, body=bm25_body)["hits"]["hits"]

    # 2) k-NN (semantic)
    knn_body = {
        "size": max(50, top_n * 5),
        "query": {
            "knn": {
                "field": "embedding",
                "query_vector": query_vec,
                "k": max(100, top_n * 10),
                "num_candidates": max(200, top_n * 20),
                "filter": {
                    "bool": { "filter": [
                        {"term": {"repo_id": repo_id}},
                        {"term": {"commit": commit}}
                    ]}
                }
            }
        }
    }
    knn = os_client.search(index=index, body=knn_body)["hits"]["hits"]

    # 3) Fuse (RRF)
    return rrf_fuse(bm25, knn, k=60, w_bm25=1.2, w_knn=1.0, top_n=top_n)
```

### C) JSON query bodies (copy/paste)

**BM25 (text)**
```json
{
  "size": 50,
  "query": {
    "bool": {
      "must": { "multi_match": { "query": "<QUERY>", "fields": ["content"], "type": "best_fields" } },
      "filter": [
        { "term": { "repo_id": "<REPO>" } },
        { "term": { "commit": "<COMMIT>" } }
      ]
    }
  }
}
```

**k-NN (semantic)**
```json
{
  "size": 50,
  "query": {
    "knn": {
      "field": "embedding",
      "query_vector": "<QUERY_VECTOR>",
      "k": 100,
      "num_candidates": 200,
      "filter": {
        "bool": { "filter": [
          { "term": { "repo_id": "<REPO>" } },
          { "term": { "commit": "<COMMIT>" } }
        ]}
      }
    }
  }
}
```

---

## SLOs & Acceptance Gates (for demo + v1)

- **Search latency:** p50 < 700 ms, p95 < 1.2 s (single-node OpenSearch hybrid).
- **E2E answer (short generation):** p95 < 2.0 s.
- **Golden questions:** ≥ 8/10 correct snippet in Top-3 with citations; >85% answerable.
- **If evidence missing:** return a candidate and flag the gap (no hallucinations).

**Scope v1:** REST + SSE only; GraphQL/WebSockets later.  
**Ingest:** JSPs/taglibs, Struts configs, controllers/services, seed/migration SQL (`ssc_*`, `items`, `ssc_item_info`, `contextual_rules`).  
**Extractors:** JSP EL/Label pairing; Struts action→JSP tracer.

---

## Bedrock Hygiene

- One Titan embed model for both indexing and queries; validate the returned dimension == `OPENSEARCH_EMBED_DIM`.
- Cache generations by `(repo, commit, prompt_hash)`.
- Enforce per-job token ceilings and spend logging.

---

## Ops Notes (Podman & K8s)

- OpenSearch local: `OPENSEARCH_JAVA_OPTS=-Xms2g -Xmx2g`, `--ulimit memlock=-1:-1`, `--ulimit nofile=65536:65536` (budget 4–8 GB RAM).
- SSE for progress; ingress-friendly. No creds in images (use env or mounted ~/.aws). IRSA/Secrets in K8s.
- TCO: self-hosting OpenSearch/MinIO assumes 0.25–0.5 FTE ops; retrieval adapter lets you switch to managed OpenSearch later.
