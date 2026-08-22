from collections import defaultdict


class ProductValidator:

    def _normalize_unit(self, unit):
        """
        Safely normalize units.
        """
        if unit is None:
            return None

        return str(unit).strip().lower()

    def _normalize_value(self, value):
        """
        Convert extracted values into a comparable form.

        Supports:
        - scalar numeric values
        - temperature ranges such as {"min": 0, "max": 80}
        """
        if isinstance(value, dict):

            minimum = value.get("min")
            maximum = value.get("max")

            return (
                "range",
                float(minimum) if minimum is not None else None,
                float(maximum) if maximum is not None else None,
            )

        if isinstance(value, (int, float)):
            return (
                "scalar",
                float(value),
            )

        return (
            "text",
            str(value).strip().lower(),
        )

    def _values_are_consistent(self, value_a, value_b):
        """
        Determine whether two extracted values are compatible.

        Important for ranges:

        0–80 °C and 80 °C are considered consistent because
        80 °C is the upper limit of the documented range.
        """

        # -----------------------------------------------------
        # Range vs range
        # -----------------------------------------------------

        if isinstance(value_a, dict) and isinstance(value_b, dict):

            min_a = value_a.get("min")
            max_a = value_a.get("max")

            min_b = value_b.get("min")
            max_b = value_b.get("max")

            return (
                min_a == min_b
                and max_a == max_b
            )

        # -----------------------------------------------------
        # Range vs scalar
        # -----------------------------------------------------

        if isinstance(value_a, dict) and not isinstance(value_b, dict):

            minimum = value_a.get("min")
            maximum = value_a.get("max")

            if minimum is None or maximum is None:
                return False

            try:
                scalar = float(value_b)
            except (TypeError, ValueError):
                return False

            return (
                float(minimum)
                <= scalar
                <= float(maximum)
            )

        if isinstance(value_b, dict) and not isinstance(value_a, dict):

            return self._values_are_consistent(
                value_b,
                value_a
            )

        # -----------------------------------------------------
        # Scalar vs scalar
        # -----------------------------------------------------

        try:
            return float(value_a) == float(value_b)
        except (TypeError, ValueError):

            return str(value_a).strip().lower() == str(
                value_b
            ).strip().lower()

    def validate(
        self,
        extracted_attributes: list[dict]
    ) -> list[dict]:

        grouped = defaultdict(list)

        # -----------------------------------------------------
        # Group evidence by attribute
        # -----------------------------------------------------

        for item in extracted_attributes:

            attribute = item.get("attribute")

            if not attribute:
                continue

            grouped[attribute].append(item)

        validated = []

        # -----------------------------------------------------
        # Validate each attribute
        # -----------------------------------------------------

        for attribute, items in grouped.items():

            if not items:
                continue

            # -------------------------------------------------
            # Normalize units
            # -------------------------------------------------

            normalized_units = [
                self._normalize_unit(
                    item.get("unit")
                )
                for item in items
            ]

            # -------------------------------------------------
            # Pages
            # -------------------------------------------------

            pages = sorted(
                set(
                    item.get("page")
                    for item in items
                    if item.get("page") is not None
                )
            )

            # -------------------------------------------------
            # Check whether all evidence is compatible
            # -------------------------------------------------

            reference_value = items[0].get("value")
            reference_unit = normalized_units[0]

            consistent = True

            for item in items[1:]:

                current_value = item.get("value")
                current_unit = self._normalize_unit(
                    item.get("unit")
                )

                # Different units are treated as a conflict.
                if current_unit != reference_unit:
                    consistent = False
                    break

                if not self._values_are_consistent(
                    reference_value,
                    current_value
                ):
                    consistent = False
                    break

            # -------------------------------------------------
            # CASE 1: Evidence agrees
            # -------------------------------------------------

            if consistent:

                evidence_count = len(items)

                if evidence_count >= 3:
                    confidence = 0.95

                elif evidence_count == 2:
                    confidence = 0.90

                else:
                    confidence = 0.80

                # Prefer a range if one exists.
                selected_value = reference_value

                for item in items:

                    value = item.get("value")

                    if isinstance(value, dict):
                        selected_value = value
                        break

                validated.append({

                    "attribute": attribute,

                    "value": selected_value,

                    "unit": reference_unit,

                    "status": "validated",

                    "confidence": confidence,

                    "evidence_count": evidence_count,

                    "pages": pages,

                    "evidence": [
                        item.get(
                            "evidence",
                            ""
                        )
                        for item in items
                    ]
                })

            # -------------------------------------------------
            # CASE 2: Conflicting evidence
            # -------------------------------------------------

            else:

                values = []

                for item in items:

                    values.append({

                        "value": item.get(
                            "value"
                        ),

                        "unit": self._normalize_unit(
                            item.get("unit")
                        ),

                        "page": item.get(
                            "page"
                        ),

                        "evidence": item.get(
                            "evidence",
                            ""
                        )
                    })

                validated.append({

                    "attribute": attribute,

                    "value": None,

                    "unit": None,

                    "status": "conflict",

                    "confidence": 0.40,

                    "evidence_count": len(items),

                    "pages": pages,

                    "values_found": values
                })

        return validated