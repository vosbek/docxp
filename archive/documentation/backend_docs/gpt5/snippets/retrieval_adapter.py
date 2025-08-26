from typing import List, Dict, Tuple

def rrf_fuse(
    bm25_hits: List[Dict],
    knn_hits: List[Dict],
    k: int = 60,
    w_bm25: float = 1.2,
    w_knn: float = 1.0,
    top_n: int = 10
) -> List[Dict]:
    """Fuse two ranked lists (BM25 & kNN) using Reciprocal Rank Fusion (RRF)."""
    def to_rank_map(hits: List[Dict]) -> Dict[str, int]:
        return {h["_id"]: i + 1 for i, h in enumerate(hits)}

    bm25_rank = to_rank_map(bm25_hits)
    knn_rank  = to_rank_map(knn_hits)

    ids = set(bm25_rank) | set(knn_rank)
    fused = []
    for _id in ids:
        s = 0.0
        if _id in bm25_rank: s += w_bm25 / (k + bm25_rank[_id])
        if _id in knn_rank:  s += w_knn  / (k + knn_rank[_id])
        fused.append((_id, s))

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


def hybrid_search(os_client, index: str, query_text: str, query_vec: list, repo_id: str, commit: str, top_n: int = 10):
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

    return rrf_fuse(bm25, knn, k=60, w_bm25=1.2, w_knn=1.0, top_n=top_n)
