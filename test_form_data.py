
import requests
import os
import uuid

BASE_URL = "http://localhost:8000"
TEST_IMAGE_PATH = "test_images/p10004457.jpeg"

def test_upload_form_data():
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"Error: test image not found at {TEST_IMAGE_PATH}")
        return

    patient_code = f"TEST_PATIENT_{uuid.uuid4().hex[:6].upper()}"
    print(f"Testing upload with Patient Code: {patient_code}")

    with open(TEST_IMAGE_PATH, "rb") as f:
        files = {"file": (os.path.basename(TEST_IMAGE_PATH), f, "image/jpeg")}
        data = {
            "patient_code": patient_code,
            "additional_info": "Form data binding test"
        }
        
        # Test the most critical endpoint
        endpoint = "/upload-complete-pipeline-with-chairman"
        print(f"Sending request to {endpoint}...")
        
        response = requests.post(f"{BASE_URL}{endpoint}", files=files, data=data)
        
        if response.ok:
            resp_data = response.json()
            returned_code = resp_data.get("patient_code")
            print(f"Success! API returned Patient Code: {returned_code}")
            
            if returned_code == patient_code:
                print("✅ VERIFICATION PASSED: Patient code correctly bound from form data.")
            else:
                print(f"❌ VERIFICATION FAILED: Expected {patient_code}, got {returned_code}")
        else:
            print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_upload_form_data()
