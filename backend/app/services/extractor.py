import re


class ProductExtractor:

    def __init__(self):

        self.patterns = {

            "pressure": [
                r"(?:maximum\s+)?(?:operating\s+)?pressure"
                r"(?:\s+is|\s*[:\-])?\s*"
                r"(\d+(?:\.\d+)?)\s*(bar|psi)"
            ],

            "flow_rate": [
                r"flow\s+rate"
                r"(?:\s+is|\s*[:\-])?\s*"
                r"(\d+(?:\.\d+)?)\s*(L/min|LPM|m3/h)"
            ],

            "motor_power": [
                r"(?:motor\s+)?power"
                r"(?:\s+is|\s*[:\-])?\s*"
                r"(\d+(?:\.\d+)?)\s*(HP|hp|kW|KW)"
            ],

            "voltage": [
                r"(?:rated\s+)?voltage"
                r"(?:\s+is|\s*[:\-])?\s*"
                r"(\d+(?:\.\d+)?)\s*(V|VAC|V\s*AC)"
            ],

            "frequency": [
                r"frequency"
                r"(?:\s+is|\s*[:\-])?\s*"
                r"(\d+(?:\.\d+)?)\s*(Hz|hz)"
            ],

            # Supports:
            # Operating Temperature 80°C
            # Operating Temperature: 80°C
            # Operating Temperature 0°C to 80°C
            "temperature": [
                r"(?:operating|fluid|ambient)?\s*temperature"
                r"(?:\s+is|\s*[:\-])?\s*"
                r"(-?\d+(?:\.\d+)?)\s*(?:°|degrees?)?\s*[Cc]"
                r"(?:\s*(?:to|-)\s*"
                r"(-?\d+(?:\.\d+)?)\s*(?:°|degrees?)?\s*[Cc])?"
            ],

            "pump_speed": [
                r"(?:pump\s+)?speed"
                r"(?:\s+is|\s*[:\-])?\s*"
                r"(\d+(?:\.\d+)?)\s*(RPM|rpm)"
            ],

            "inlet_connection": [
                r"inlet\s+connection"
                r"(?:\s+is|\s*[:\-])?\s*"
                r"(\d+(?:\.\d+)?)\s*mm"
            ],

            "outlet_connection": [
                r"outlet\s+connection"
                r"(?:\s+is|\s*[:\-])?\s*"
                r"(\d+(?:\.\d+)?)\s*mm"
            ],

            "warranty": [
                r"warranty"
                r"(?:\s+period|\s+is|\s*[:\-])?\s*"
                r"(\d+(?:\.\d+)?)\s*(months?|years?)"
            ]
        }

        self.table_patterns = {

            "pressure": (
                r"pressure\s*[\r\n]+\s*"
                r"(\d+(?:\.\d+)?)\s*(bar|psi)"
            ),

            "flow_rate": (
                r"flow\s+rate\s*[\r\n]+\s*"
                r"(\d+(?:\.\d+)?)\s*(L/min|LPM|m3/h)"
            ),

            "motor_power": (
                r"motor\s+power\s*[\r\n]+\s*"
                r"(\d+(?:\.\d+)?)\s*(HP|hp|kW|KW)"
            ),

            "voltage": (
                r"voltage\s*[\r\n]+\s*"
                r"(\d+(?:\.\d+)?)\s*(V|VAC|V\s*AC)"
            ),

            "frequency": (
                r"frequency\s*[\r\n]+\s*"
                r"(\d+(?:\.\d+)?)\s*(Hz|hz)"
            ),

            "temperature": (
                r"(?:operating|fluid|ambient)?\s*temperature"
                r"\s*[\r\n]+\s*"
                r"(-?\d+(?:\.\d+)?)\s*(?:°|degrees?)?\s*[Cc]"
                r"(?:\s*(?:to|-)\s*"
                r"(-?\d+(?:\.\d+)?)\s*(?:°|degrees?)?\s*[Cc])?"
            ),

            "pump_speed": (
                r"pump\s+speed\s*[\r\n]+\s*"
                r"(\d+(?:\.\d+)?)\s*(RPM|rpm)"
            ),

            "inlet_connection": (
                r"inlet\s+connection\s*[\r\n]+\s*"
                r"(\d+(?:\.\d+)?)\s*mm"
            ),

            "outlet_connection": (
                r"outlet\s+connection\s*[\r\n]+\s*"
                r"(\d+(?:\.\d+)?)\s*mm"
            ),

            "warranty": (
                r"warranty\s*[\r\n]+\s*"
                r"(\d+(?:\.\d+)?)\s*(months?|years?)"
            )
        }

    def _add_result(
        self,
        results,
        attribute,
        value,
        unit,
        evidence,
        range_end=None
    ):

        if attribute == "temperature" and range_end is not None:

            results.append({
                "attribute": attribute,
                "value": {
                    "min": float(value),
                    "max": float(range_end)
                },
                "unit": unit,
                "evidence": evidence.strip()
            })

        else:

            results.append({
                "attribute": attribute,
                "value": float(value),
                "unit": unit,
                "evidence": evidence.strip()
            })

    def extract_numeric_attributes(
        self,
        text: str
    ) -> list[dict]:

        results = []

        # Normalize PDF line endings
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        # -----------------------------------------
        # 1. Sentence / inline extraction
        # -----------------------------------------

        for attribute, patterns in self.patterns.items():

            for pattern in patterns:

                matches = re.finditer(
                    pattern,
                    text,
                    flags=re.IGNORECASE
                )

                for match in matches:

                    groups = match.groups()

                    if attribute == "temperature":

                        if len(groups) < 1:
                            continue

                        # Temperature always uses Celsius.
                        # If there is a range, groups[1] is
                        # the upper bound.
                        self._add_result(
                            results,
                            attribute,
                            groups[0],
                            "°C",
                            match.group(0),
                            groups[1] if len(groups) > 1 else None
                        )

                    else:

                        if len(groups) < 2:
                            continue

                        self._add_result(
                            results,
                            attribute,
                            groups[0],
                            groups[1],
                            match.group(0)
                        )

        # -----------------------------------------
        # 2. PDF table extraction
        # -----------------------------------------

        for attribute, pattern in self.table_patterns.items():

            matches = re.finditer(
                pattern,
                text,
                flags=re.IGNORECASE
            )

            for match in matches:

                groups = match.groups()

                if attribute == "temperature":

                    if len(groups) < 1:
                        continue

                    self._add_result(
                        results,
                        attribute,
                        groups[0],
                        "°C",
                        match.group(0),
                        groups[1] if len(groups) > 1 else None
                    )

                else:

                    if len(groups) < 2:
                        continue

                    self._add_result(
                        results,
                        attribute,
                        groups[0],
                        groups[1],
                        match.group(0)
                    )

        # -----------------------------------------
        # 3. Remove duplicates
        # -----------------------------------------

        unique_results = []

        seen = set()

        for result in results:

            value = result["value"]

            if isinstance(value, dict):
                value_key = (
                    value.get("min"),
                    value.get("max")
                )
            else:
                value_key = value

            key = (
                result["attribute"],
                value_key,
                result["unit"]
            )

            if key not in seen:

                seen.add(key)
                unique_results.append(result)

        return unique_results