import re
import json

def extract_pressure(command):
    if command["action"] == "gauge detected":
        match = re.search(r"pressure: ([\d.]+) bar; image position", command["content"])
        if match:
            pressure = float(match.group(1))
            print(f"Extracted pressure: {pressure} bar")
        else:
            print("No pressure detected in gauge")

example_message_1 = {"action": "gauge detected", "content": "pressure: 2.91 bar; image position (963, 531) px; frame 13809."}
example_message_2 = {"action": "gauge detected", "content": "pressure unavailable (awaiting confirmation); image position (815, 435.5) px; frame 187."}
example_message_3 = {"action": "gauge detected", "content": "pressure unavailable (awaiting confirmation); image position (815, 435.5) px; frame 187."}
example_message_4 = {"action": "gauge detected", "content": "pressure: 67.67 bar; image position (963, 531) px; frame 13809."}

examples = [example_message_1, example_message_2, example_message_3, example_message_4]

for example in examples:
    extract_pressure(example)


