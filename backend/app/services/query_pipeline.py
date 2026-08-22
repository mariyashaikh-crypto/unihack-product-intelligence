from app.services.retriever import ProductRetriever
from app.services.extractor import ProductExtractor
from app.services.validator import ProductValidator


class ProductQueryPipeline:

    RELEVANCE_THRESHOLD = 0.05

    def __init__(self, chunks: list[dict]):
        self.retriever = ProductRetriever(chunks)
        self.extractor = ProductExtractor()
        self.validator = ProductValidator()

    def _is_numeric_query(self, question: str) -> bool:
        numeric_terms = [
            "pressure", "flow", "flow rate", "capacity",
            "power", "motor power", "voltage", "frequency",
            "temperature", "speed", "rpm", "warranty",
        ]

        q = question.lower()

        return any(
            term in q
            for term in numeric_terms
        )

    def _no_evidence(self, question: str) -> dict:
        return {
            "question": question,
            "answer": None,
            "status": "no_evidence",
            "confidence": 0.0,
            "evidence": [],
        }

    def _has_relevant_evidence(
        self,
        question: str,
        retrieved: list[dict],
    ) -> bool:

        if not retrieved:
            return False

        best = max(
            item.get("similarity", 0.0)
            for item in retrieved
        )

        return best >= self.RELEVANCE_THRESHOLD

    def _build_numeric_answer(
        self,
        question: str,
        retrieved: list[dict],
    ) -> dict:

        if not self._has_relevant_evidence(
            question,
            retrieved,
        ):
            return self._no_evidence(question)

        extracted = []

        for chunk in retrieved:

            values = self.extractor.extract_numeric_attributes(
                chunk.get("text", "")
            )

            for value in values:

                item = value.copy()

                item["page"] = chunk.get("page")
                item["similarity"] = chunk.get(
                    "similarity",
                    0.0
                )

                extracted.append(item)

        if not extracted:

            return self._no_evidence(question)

        validated = self.validator.validate(
            extracted
        )

        if not validated:

            return self._no_evidence(question)

        # Prefer the attribute matched by retrieval.
        matched_attribute = None

        for chunk in retrieved:

            if chunk.get("matched_attribute"):
                matched_attribute = chunk[
                    "matched_attribute"
                ]
                break

        if matched_attribute:

            matching = [
                item
                for item in validated
                if item.get("attribute")
                == matched_attribute
            ]

            if matching:
                validated = matching

        first = validated[0]

        return {
            "question": question,
            "answer": first,
            "status": "success",
            "confidence": round(
                first.get(
                    "confidence",
                    0.0
                ),
                4,
            ),
            "evidence": validated,
        }

    def _extract_generic_answer(
        self,
        question: str,
        retrieved: list[dict],
    ) -> str:

        """
        Generic text answering without relying on a fixed
        attribute vocabulary.

        Uses the highest-ranked chunk and trims obvious
        document noise.
        """

        if not retrieved:
            return ""

        text = retrieved[0].get(
            "text",
            ""
        ).strip()

        if not text:
            return ""

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        if not lines:
            return text

        q = question.lower()

        # Questions asking for a name/title/event.
        if any(
            phrase in q
            for phrase in [
                "name",
                "title",
                "event",
                "topic",
                "subject",
            ]
        ):

            candidates = []

            for line in lines:

                letters = [
                    c for c in line
                    if c.isalpha()
                ]

                if not letters:
                    continue

                uppercase_ratio = (
                    sum(
                        1
                        for c in letters
                        if c.isupper()
                    )
                    / len(letters)
                )

                if (
                    uppercase_ratio >= 0.55
                    and 8 <= len(line) <= 180
                ):
                    candidates.append(line)

            if candidates:
                return "\n".join(
                    candidates[:3]
                )

        # For "when" questions, prefer lines with date/time.
        if any(
            word in q
            for word in [
                "when",
                "date",
                "time",
            ]
        ):

            candidates = [
                line
                for line in lines
                if any(
                    char.isdigit()
                    for char in line
                )
            ]

            if candidates:
                return "\n".join(
                    candidates[:5]
                )

        # For "where" questions, prefer venue/location-like lines.
        if any(
            word in q
            for word in [
                "where",
                "venue",
                "location",
            ]
        ):

            candidates = [
                line
                for line in lines
                if any(
                    term in line.lower()
                    for term in [
                        "hall",
                        "college",
                        "institute",
                        "road",
                        "street",
                        "solapur",
                        "pune",
                        "venue",
                    ]
                )
            ]

            if candidates:
                return "\n".join(
                    candidates[:5]
                )

        # For who/speaker/organizer questions.
        if any(
            word in q
            for word in [
                "who",
                "speaker",
                "speakers",
                "organized",
                "organizer",
                "host",
            ]
        ):

            candidates = [
                line
                for line in lines
                if (
                    len(line.split()) <= 12
                    and any(
                        c.isalpha()
                        for c in line
                    )
                )
            ]

            if candidates:
                return "\n".join(
                    candidates[:8]
                )

        # General question: return the most relevant
        # chunk rather than pretending to synthesize.
        return text

    def _build_generic_answer(
        self,
        question: str,
        retrieved: list[dict],
    ) -> dict:

        if not self._has_relevant_evidence(
            question,
            retrieved,
        ):
            return self._no_evidence(question)

        answer = self._extract_generic_answer(
            question,
            retrieved,
        )

        if not answer:
            return self._no_evidence(question)

        confidence = retrieved[0].get(
            "similarity",
            0.0
        )

        return {
            "question": question,
            "answer": answer,
            "status": "success",
            "confidence": round(
                confidence,
                4
            ),
            "source_page": retrieved[0].get(
                "page"
            ),
            "evidence": [
                {
                    "page": item.get("page"),
                    "similarity": item.get(
                        "similarity",
                        0.0
                    ),
                    "text": item.get(
                        "text",
                        ""
                    ),
                }
                for item in retrieved[:3]
            ],
        }

    def query(
        self,
        question: str,
        top_k: int = 5,
    ) -> dict:

        question = question.strip()

        if not question:
            return {
                "question": question,
                "answer": None,
                "status": "invalid_question",
                "confidence": 0.0,
                "evidence": [],
            }

        retrieved = self.retriever.search(
            question,
            top_k=top_k,
        )

        if not retrieved:
            return self._no_evidence(
                question
            )

        if self._is_numeric_query(question):
            return self._build_numeric_answer(
                question,
                retrieved,
            )

        return self._build_generic_answer(
            question,
            retrieved,
        )