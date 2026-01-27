import os
import requests
from data.paths import EMBED_SERVICE_URL

# get the embed service url first from env (for Docker), if not, use EMBED_SERVICE_URL
embed_service_url = os.getenv("EMBED_SERVICE_URL", EMBED_SERVICE_URL)

# TODO: call the embedding service with API
def embed_query(text: str) -> list[float]:
    resp = requests.post(f"{embed_service_url}/embed", json={"input": text})
    resp.raise_for_status() #cecks the HTTP status code and raises an exception if the request failed
    return resp.json()["embeddings"][0]

def embed_documents(texts: list[str]) -> list[float]:
    resp = requests.post(f"{embed_service_url}/embed", json={"input": texts})
    resp.raise_for_status()
    return resp.json()["embeddings"]

# Example usage
if __name__ == "__main__":
    emb = embed_query("你哪位")
    print(f"{len(emb)}")  # Should be 1024
    print(f"{emb}")

    emb_doc = embed_documents(["这是谁", "这是你"])
    print(f"{len(emb_doc)}") # Should be 2
    print(f"{emb_doc}")