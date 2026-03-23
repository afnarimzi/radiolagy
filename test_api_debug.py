
import requests
import json

BASE_URL = "http://localhost:8000"
CASE_ID = "387a6569-88c5-4936-8f97-9cc7bb0a7952"

def test_api():
    with open("c:\\MM_internship\\radilolagy\\MM-DUK-Interns\\test_api_output.txt", "w") as f:
        f.write(f"Testing API for Case ID: {CASE_ID}\n")
        try:
            response = requests.get(f"{BASE_URL}/cases/{CASE_ID}")
            if response.ok:
                data = response.json()
                f.write("\n--- API Response Structure ---\n")
                for key in data:
                    val = data[key]
                    val_type = type(val)
                    f.write(f"Key: {key} | Type: {val_type}\n")
                    if isinstance(val, str) and (val.startswith('{') or val.startswith('[')):
                        f.write(f"  WARNING: Key {key} identifies as string but looks like JSON: {val[:100]}...\n")
                    elif key in ["chairman_report", "radiology_analysis"]:
                         f.write(f"  {key}: {val}\n")
            else:
                f.write(f"Error: {response.status_code} - {response.text}\n")
        except Exception as e:
            f.write(f"ERROR: {e}\n")
    print("Done writing to test_api_output.txt")

if __name__ == "__main__":
    test_api()
