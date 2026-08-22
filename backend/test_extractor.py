from app.services.extractor import ProductExtractor


extractor = ProductExtractor()


test_text = """
The maximum operating pressure is 12 bar.
The flow rate is 450 L/min.
The motor power is 5 HP.
The rated voltage is 415 V AC.
The frequency is 50 Hz.
The operating temperature is 80°C.
The pump speed is 1450 RPM.
The inlet connection is 80 mm.
The outlet connection is 65 mm.
The standard manufacturer warranty period is 24 months.
"""


results = extractor.extract_numeric_attributes(test_text)


print("\n========== EXTRACTED ATTRIBUTES ==========\n")

if not results:
    print("No attributes were extracted.")

else:
    for result in results:
        print(result)