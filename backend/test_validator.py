from app.services.validator import ProductValidator


validator = ProductValidator()


test_data = [

    {
        "attribute": "pressure",
        "value": 12,
        "unit": "bar",
        "page": 1,
        "evidence": "Maximum Operating Pressure 12 bar"
    },

    {
        "attribute": "pressure",
        "value": 12,
        "unit": "bar",
        "page": 2,
        "evidence": "maximum operating pressure is 12 bar"
    },

    {
        "attribute": "pressure",
        "value": 12,
        "unit": "bar",
        "page": 3,
        "evidence": "maximum operating pressure is 12 bar"
    },

    {
        "attribute": "motor_power",
        "value": 5,
        "unit": "HP",
        "page": 1,
        "evidence": "Motor Power 5 HP"
    },

    {
        "attribute": "motor_power",
        "value": 5,
        "unit": "HP",
        "page": 3,
        "evidence": "motor power is 5 HP"
    },

    {
        "attribute": "voltage",
        "value": 415,
        "unit": "V",
        "page": 1,
        "evidence": "Rated Voltage 415 V"
    }
]


results = validator.validate(test_data)


print("\n========== VALIDATION RESULTS ==========\n")


for result in results:

    print(f"Attribute: {result['attribute']}")
    print(f"Value: {result['value']} {result['unit']}")
    print(f"Status: {result['status']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Evidence Count: {result['evidence_count']}")
    print(f"Pages: {result['pages']}")

    if "evidence" in result:
        print("Evidence:")
        for evidence in result["evidence"]:
            print(f"  - {evidence}")

    print("-" * 50)