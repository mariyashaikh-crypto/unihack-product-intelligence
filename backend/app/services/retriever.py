from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class ProductRetriever:

    def __init__(self, chunks: list[dict]):

        self.chunks = chunks

        self.documents = [
            chunk.get("text", "")
            for chunk in chunks
        ]

        if not self.documents:
            self.vectorizer = None
            self.vectors = None
            return

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 3),
            sublinear_tf=True,
            min_df=1,
        )

        self.vectors = self.vectorizer.fit_transform(
            self.documents
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:

        if not query.strip():
            return []

        if self.vectorizer is None:
            return []

        query_vector = self.vectorizer.transform(
            [query]
        )

        scores = cosine_similarity(
            query_vector,
            self.vectors
        )[0]

        results = []

        for index, score in enumerate(scores):

            chunk = self.chunks[index].copy()

            chunk["similarity"] = round(
                float(score),
                4,
            )

            results.append(chunk)

        results.sort(
            key=lambda item: item["similarity"],
            reverse=True,
        )

        return results[:top_k]