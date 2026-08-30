import chromadb
from chromadb.errors import NotFoundError


def get_chroma_client() -> chromadb.PersistentClient:
    """Return PersistentClient with storage at ./chroma_db/"""
    return chromadb.PersistentClient(path="./chroma_db")


def reset_collection(client: chromadb.PersistentClient, name: str) -> chromadb.Collection:
    """Delete collection if exists, then create fresh.

    Uses Chroma's default embedding function. Re-running ingestion replaces
    the collection to avoid duplicate chunks with split scores.
    """
    try:
        client.delete_collection(name=name)
    except (ValueError, NotFoundError):
        pass

    return client.create_collection(
        name=name,
        metadata={"description": "Acme auto insurance corpus"}
    )
