import os
import requests
from config.setting import settings

# get the embed service url first from env (for Docker), if not, use EMBED_SERVICE_URL
embed_service_url = os.getenv("EMBED_SERVICE_URL", settings.EMBED_SERVICE_URL)
embed_service_port1 = os.getenv("EMBED_SERVICE_PORT1", settings.EMBED_SERVICE_PORT1)
embed_service_port2 = os.getenv("EMBED_SERVICE_PORT2", settings.EMBED_SERVICE_PORT2)

# TODO: call the embedding service with API

def embed_documents(texts: list[str]) -> list[list[float]]:
    """
    embed_documents only for preparing embeddings to insert to vector database during model initialization
    """
    resp = requests.post(f"{embed_service_url}:{embed_service_port1}/embed", json={"input": texts})
    resp.raise_for_status()
    return resp.json()["embeddings"]

def embed_query(text: str) -> list[float]:
    """
    embed_query only for embedding user queries during tasks
    """
    resp = requests.post(f"{embed_service_url}:{embed_service_port2}/embed", json={"input": text})
    resp.raise_for_status() #checks the HTTP status code and raises an exception if the request failed
    return resp.json()["embeddings"][0]


# Example usage
if __name__ == "__main__":
    emb = embed_query("我见过你吗")
    print(f"{len(emb)}")  # Should be 1024
    print(f"{emb}")

    emb_doc = embed_documents(["这是谁", "这是你"])
    print(f"{len(emb_doc)}") # Should be 2
    print(f"{emb_doc}")