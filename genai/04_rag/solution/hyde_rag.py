"""
Solution: HyDE — Hypothetical Document Embeddings

Improves RAG retrieval by embedding a hypothetical answer rather than the raw question.
This bridges the vocabulary gap between question-space and document-space embeddings.
"""

from openai import OpenAI
from labs.rag_pipeline import embed, retrieve  # Reuse from lab

client = OpenAI()


def generate_hypothetical_answer(query: str) -> str:
    """
    Ask the LLM to write a hypothetical answer to the query.
    This answer doesn't need to be factually correct —
    it just needs to look like the kind of document we're searching in.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Write a 2-3 sentence answer to the question as if you are an expert. "
                    "Use formal, technical language similar to documentation or academic writing. "
                    "This will be used as a search query — accuracy is not critical."
                ),
            },
            {"role": "user", "content": query},
        ],
        temperature=0,
        max_tokens=150,
    )
    return response.choices[0].message.content.strip()


def hyde_retrieve(query: str, top_k: int = 3) -> dict:
    """
    Retrieve using Hypothetical Document Embeddings (HyDE).
    Returns results from both standard and HyDE retrieval for comparison.
    """
    # Standard retrieval (embed the question directly)
    standard_results = retrieve(query, top_k=top_k)

    # HyDE retrieval
    hypothetical_answer = generate_hypothetical_answer(query)
    print(f"\n🤔 Hypothetical Answer Generated:\n  '{hypothetical_answer}'")

    # Embed the hypothetical answer instead of the original question
    hyp_embedding = embed(hypothetical_answer)

    # Search using the hypothetical embedding
    # (In practice, call your vector DB with the embedding directly)
    # For this demo, we simulate by retrieving using the hypothetical as a "query"
    hyde_results = retrieve(hypothetical_answer, top_k=top_k)

    return {
        "query": query,
        "hypothetical_answer": hypothetical_answer,
        "standard_results": standard_results,
        "hyde_results": hyde_results,
    }


if __name__ == "__main__":
    query = "What is RAG and why does it reduce hallucinations?"

    print(f"Query: {query}\n")
    results = hyde_retrieve(query)

    print("\n--- Standard Retrieval ---")
    for r in results["standard_results"]:
        print(f"  [{r['source']}] Sim: {r['similarity']:.4f} | {r['content'][:80]}...")

    print("\n--- HyDE Retrieval ---")
    for r in results["hyde_results"]:
        print(f"  [{r['source']}] Sim: {r['similarity']:.4f} | {r['content'][:80]}...")

    print("\nNote: HyDE typically improves similarity scores for complex queries.")
