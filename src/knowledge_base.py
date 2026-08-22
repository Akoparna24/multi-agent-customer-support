import os
import weaviate
from weaviate.auth import AuthApiKey
from dotenv import load_dotenv
from rich.console import Console
import weaviate.classes.config as wc

load_dotenv()
console = Console()

from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def get_weaviate_client():
    """Connect to Weaviate cloud cluster."""
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=os.getenv("WEAVIATE_URL"),
        auth_credentials=AuthApiKey(os.getenv("WEAVIATE_API_KEY"))
    )
    console.print("Weaviate connected!")
    return client

def create_collections(client):
    """Create single SupportDocs collection with domain field."""

    if client.collections.exists("SupportDocs"):
        console.print("SupportDocs already exists — skipping")
        return

    client.collections.create(
        name="SupportDocs",
        vector_config=wc.Configure.Vectors.self_provided(
            name="default"
        ),
        properties=[
            wc.Property(name="content",  data_type=wc.DataType.TEXT),
            wc.Property(name="source",   data_type=wc.DataType.TEXT),
            wc.Property(name="domain",   data_type=wc.DataType.TEXT),
        ]
    )
    console.print("Created collection: SupportDocs")


def ingest_documents(client):
    """Read documents from data folders and store in Weaviate."""

    collection = client.collections.get("SupportDocs")

    # Map domain to file path
    domain_files = {
        "billing": "data/billing_docs/billing_faq.txt",
        "technical": "data/tech_docs/tech_faq.txt",
        "general": "data/general_docs/general_faq.txt",
    }

    for domain, file_path in domain_files.items():
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split by double newline into paragraphs
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        for paragraph in paragraphs:
            # Generate embedding
            vector = embedding_model.encode(paragraph).tolist()

            # Insert into Weaviate
            collection.data.insert(
                properties={
                    "content": paragraph,
                    "source": file_path,
                    "domain": domain,
                },
                vector={"default": vector}
            )

        console.print(f"Ingested {len(paragraphs)} chunks from {domain}")

def search_documents(client, query: str, domain: str = None, limit: int = 3) -> list[dict]:
    """Search SupportDocs collection by semantic similarity."""
    from weaviate.classes.query import Filter, MetadataQuery

    collection = client.collections.get("SupportDocs")

    # Generate query embedding
    query_vector = embedding_model.encode(query).tolist()

    # Build filter if domain specified
    filters = None
    if domain:
        filters = Filter.by_property("domain").equal(domain)

    results = collection.query.near_vector(
        near_vector=query_vector,
        limit=limit,
        filters=filters,
        return_metadata=MetadataQuery(distance=True)
    )

    formatted = []
    for obj in results.objects:
        formatted.append({
            "content": obj.properties["content"],
            "domain":  obj.properties["domain"],
            "score":   round(1 - obj.metadata.distance, 4),
        })

    return formatted