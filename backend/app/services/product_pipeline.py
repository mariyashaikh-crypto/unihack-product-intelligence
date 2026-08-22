from app.services.extractor import ProductExtractor
from app.services.retriever import ProductRetriever
from app.services.validator import ProductValidator


class ProductPipeline:

    def __init__(
        self,
        chunks: list[dict],
        extracted_attributes: list[dict]
    ):
        self.chunks = chunks

        self.retriever = ProductRetriever(chunks)

        self.extractor = ProductExtractor()

        self.validator = ProductValidator()

        self.extracted_attributes = extracted_attributes

    def _extract_application_answer(
        self,
        retrieved: list[dict]
    ) -> str | None:

        for result in retrieved:

            text = result["text"]

            marker = "4. Applications"

            lower_text = text.lower()

            start = lower_text.find(
                marker.lower()
            )

            if start == -1:
                continue

            section_text = text[start:]

            next_sections = [
                "5. Operating Conditions",
                "6. Installation Requirements",
                "7. Maintenance",
                "8. Safety Notes",
                "9. Warranty",
                "10. Product Data",
            ]

            lower_section = section_text.lower()

            end_positions = []

            for section in next_sections:

                position = lower_section.find(
                    section.lower()
                )

                if position > 0:
                    end_positions.append(position)

            if end_positions:

                section_text = section_text[
                    :min(end_positions)
                ]

            return section_text.strip()

        return None

    def _build_concise_evidence(
        self,
        attribute: str,
        value: float,
        unit: str
    ) -> list[dict]:

        evidence = []

        for item in self.extracted_attributes:

            if item["attribute"] != attribute:
                continue

            if float(item["value"]) != float(value):
                continue

            if item["unit"].lower() != unit.lower():
                continue

            evidence.append({
                "page": item.get("page"),
                "text": item["evidence"],
                "value": item["value"],
                "unit": item["unit"],
            })

        # Remove duplicate page/evidence combinations.

        unique = []

        seen = set()

        for item in evidence:

            key = (
                item["page"],
                item["text"].lower()
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(item)

        return unique

    def _find_requested_attribute(
        self,
        question: str
    ) -> str | None:

        question = question.lower()

        attribute_terms = {
            "pressure": [
                "pressure",
                "operating pressure",
                "maximum pressure",
            ],

            "flow_rate": [
                "flow",
                "flow rate",
                "capacity",
            ],

            "motor_power": [
                "motor power",
                "horsepower",
                "power",
            ],

            "voltage": [
                "voltage",
                "rated voltage",
            ],

            "frequency": [
                "frequency",
            ],

            "temperature": [
                "temperature",
                "operating temperature",
                "fluid temperature",
                "ambient temperature",
            ],

            "pump_speed": [
                "pump speed",
                "speed",
            ],

            "inlet_connection": [
                "inlet connection",
                "inlet",
            ],

            "outlet_connection": [
                "outlet connection",
                "outlet",
            ],

            "warranty": [
                "warranty",
            ],
        }

        # Check longer phrases first.

        for attribute, terms in attribute_terms.items():

            terms = sorted(
                terms,
                key=len,
                reverse=True
            )

            for term in terms:

                if term in question:
                    return attribute

        return None

    def _build_numeric_answer(
        self,
        question: str,
        retrieved: list[dict]
    ) -> dict | None:

        requested_attribute = (
            self._find_requested_attribute(
                question
            )
        )

        if not requested_attribute:
            return None

        matches = []

        for result in retrieved:

            extracted = (
                self.extractor
                .extract_numeric_attributes(
                    result["text"]
                )
            )

            for item in extracted:

                if (
                    item["attribute"]
                    == requested_attribute
                ):
                    matches.append(item)

        if not matches:
            return None

        first = matches[0]

        value = first["value"]
        unit = first["unit"]

        concise_evidence = (
            self._build_concise_evidence(
                requested_attribute,
                value,
                unit
            )
        )

        pages = sorted(
            set(
                item["page"]
                for item in concise_evidence
                if item["page"] is not None
            )
        )

        # If the extracted page evidence is available,
        # use the number of unique supporting items.

        evidence_count = len(
            concise_evidence
        )

        # Confidence is based on the amount of
        # independent supporting evidence.

        if evidence_count >= 3:
            confidence = 1.0

        elif evidence_count == 2:
            confidence = 0.95

        else:
            confidence = 0.85

        return {
            "attribute": requested_attribute,
            "value": value,
            "unit": unit,
            "status": "validated",
            "confidence": confidence,
            "pages": pages,
            "evidence_count": evidence_count,
            "evidence": concise_evidence,
        }

    def query(
        self,
        question: str,
        top_k: int = 3
    ) -> dict:

        retrieved = self.retriever.search(
            question,
            top_k=top_k
        )

        if not retrieved:

            return {
                "status": "no_results",
                "confidence": 0.0,
                "answer": None,
                "evidence": [],
            }

        question_lower = question.lower()

        is_application_query = any(
            phrase in question_lower
            for phrase in [
                "application",
                "applications",
                "product applications",
                "use case",
                "used for",
                "suitable for",
            ]
        )

        # -----------------------------------------
        # APPLICATION QUERY
        # -----------------------------------------

        if is_application_query:

            application_answer = (
                self._extract_application_answer(
                    retrieved
                )
            )

            if application_answer:

                confidence = retrieved[0][
                    "similarity"
                ]

                return {
                    "status": "success",
                    "confidence": confidence,
                    "answer": application_answer,
                    "evidence": [
                        {
                            "page": item["page"],
                            "similarity": item[
                                "similarity"
                            ],
                            "text": application_answer,
                        }
                        for item in retrieved
                        if (
                            "4. Applications"
                            .lower()
                            in item["text"].lower()
                        )
                    ],
                }

        # -----------------------------------------
        # NUMERIC ATTRIBUTE QUERY
        # -----------------------------------------

        numeric_answer = (
            self._build_numeric_answer(
                question,
                retrieved
            )
        )

        if numeric_answer:

            return {
                "status": "success",
                "confidence": numeric_answer[
                    "confidence"
                ],
                "answer": numeric_answer,
                "evidence": numeric_answer[
                    "evidence"
                ],
            }

        # -----------------------------------------
        # FALLBACK
        # -----------------------------------------

        return {
            "status": "success",
            "confidence": retrieved[0][
                "similarity"
            ],
            "answer": retrieved[0]["text"],
            "evidence": [
                {
                    "page": item["page"],
                    "similarity": item[
                        "similarity"
                    ],
                    "text": item["text"],
                }
                for item in retrieved
            ],
        }