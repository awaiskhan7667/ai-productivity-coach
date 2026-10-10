from sentence_transformers import SentenceTransformer
import faiss
from openai import OpenAI
from config import settings
import numpy as np


client = OpenAI(
    api_key=settings.openai_api_key
)



embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def create_embeddings(chunks):
    embeddings = embedding_model.encode(chunks)
    return np.array(embeddings).astype("float32")

def generate_rag_answer(question: str, context: list):

    prompt = f"""
Answer the user's question using ONLY the context below.

Context:
{context}

Question:
{question}

If the answer is not in the context, say:
"I don't know based on your notes."
"""

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt
    )

    return response.output_text

def create_vector_index(embeddings):
    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    return index


def build_index(chunks):
    embeddings = create_embeddings(chunks)
    index = create_vector_index(embeddings)

    return index, chunks


def search_chunks(query, index, chunks, top_k=3, threshold=1.0):
    query_embedding = create_embeddings([query])

    distances, indices = index.search(
        query_embedding,
        top_k
    )

    results = []

    for distance, i in zip(distances[0], indices[0]):
        if distance <= threshold:
            results.append(chunks[i])

    return results


notes = [
    "I study FastAPI in the morning.",
    "I work on my AI project in the afternoon.",
    "I review Python concepts in the evening.",
    "My main goal is to become an AI Engineer."
]


index, chunks = build_index(notes)

def search_user_notes(question: str):

    results = search_chunks(
        question,
        index,
        chunks
    )

    if not results:
        return "I don't know based on your notes."

    return generate_rag_answer(
        question,
        results
    )