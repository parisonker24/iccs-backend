import os
import asyncio
import numpy as np

# Prefer sklearn's implementation when available, but provide a lightweight
# numpy-based fallback so tests and imports don't fail in minimal envs.
try:
    from sklearn.metrics.pairwise import cosine_similarity  # type: ignore
except Exception:
    def cosine_similarity(a, b):
        """Compute cosine similarity between 2D arrays `a` and `b`.

        This mimics sklearn.metrics.pairwise.cosine_similarity for the
        small usage in this project (pairwise between two vectors).
        """
        a_arr = np.asarray(a, dtype=float)
        b_arr = np.asarray(b, dtype=float)
        # normalize rows
        def _norm_rows(x):
            norms = np.linalg.norm(x, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            return x / norms

        a_n = _norm_rows(a_arr)
        b_n = _norm_rows(b_arr)
        return np.dot(a_n, b_n.T)


class EmbeddingService:
    """Wrapper around OpenAI embeddings client.

    Initialization requires an API key either passed directly or through
    the `OPENAI_API_KEY` environment variable. If the key is missing the
    constructor raises ValueError (tests expect this behaviour).
    """

    def __init__(self, api_key: str | None = None):
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY not set")
        try:
            from openai import OpenAI
        except Exception as e:
            raise ImportError("openai package is required for EmbeddingService") from e

        self.client = OpenAI(api_key=key)

    async def get_embedding(self, text: str) -> np.ndarray:
        def _call():
            resp = self.client.embeddings.create(model="text-embedding-3-small", input=text)
            return np.array(resp.data[0].embedding)

        return await asyncio.to_thread(_call)

    async def match_products(self, new_product: str, existing_product: str):
        emb1 = await self.get_embedding(new_product)
        emb2 = await self.get_embedding(existing_product)

        similarity = cosine_similarity([emb1], [emb2])[0][0]

        if similarity > 0.85:
            label = "High Similarity - Possible Duplicate"
        elif similarity > 0.65:
            label = "Medium Similarity - Needs Review"
        else:
            label = "Low Similarity - New Product"

        return {"similarity_score": round(float(similarity), 3), "confidence_label": label}


async def get_embedding(text: str) -> np.ndarray:
    svc = EmbeddingService()
    return await svc.get_embedding(text)


async def match_products(new_product: str, existing_product: str):
    svc = EmbeddingService()
    return await svc.match_products(new_product, existing_product)


def get_openai_client(api_key: str | None = None):
    """Return an OpenAI client instance using the provided API key or
    the `OPENAI_API_KEY` environment variable. This is a convenience for
    modules that need direct access to the OpenAI client (e.g. product_matcher).
    """
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY not set")
    try:
        from openai import OpenAI
    except Exception as e:
        raise ImportError("openai package is required to get an OpenAI client") from e

    return OpenAI(api_key=key)
