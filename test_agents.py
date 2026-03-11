"""
Test file for Clinical Agent and Evidence Agent
Run from radiolagy/ directory:
    python test_agents.py
    python test_agents.py clinical
    python test_agents.py evidence
    python test_agents.py both
"""
import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

# ── Test Colors ──────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def print_header(title):
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}  {title}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}")

def print_pass(msg):
    print(f"{GREEN}  ✅ PASS: {msg}{RESET}")

def print_fail(msg):
    print(f"{RED}  ❌ FAIL: {msg}{RESET}")

def print_info(msg):
    print(f"{YELLOW}  ℹ  {msg}{RESET}")

def print_result(key, value):
    print(f"  {BOLD}{key}:{RESET} {value}")


# ── Test Cases ───────────────────────────────────────────
TEST_CASES = [
    {
        "name": "Normal chest X-ray",
        "clinical_input": {
            "case_id": f"TEST_NORMAL_{datetime.now().strftime('%H%M%S')}",
            "patient_code": "TEST_001",
            "radiology_findings": "Normal chest X-ray. No acute cardiopulmonary findings. Clear lung fields bilaterally.",
            "abnormalities": [],
            "confidence": 0.95
        }
    },
    {
        "name": "Pneumonia case",
        "clinical_input": {
            "case_id": f"TEST_PNEUMONIA_{datetime.now().strftime('%H%M%S')}",
            "patient_code": "TEST_002",
            "radiology_findings": "Increased opacity in right lower lobe. Possible consolidation. No pleural effusion detected.",
            "abnormalities": ["consolidation", "opacity"],
            "confidence": 0.85
        }
    },
    {
        "name": "Critical case",
        "clinical_input": {
            "case_id": f"TEST_CRITICAL_{datetime.now().strftime('%H%M%S')}",
            "patient_code": "TEST_003",
            "radiology_findings": "Large pneumothorax detected on left side. Mediastinal shift to the right. Tension pneumothorax suspected.",
            "abnormalities": ["pneumothorax", "mediastinal shift"],
            "confidence": 0.92
        }
    }
]


# ── Clinical Agent Tests ─────────────────────────────────
def test_clinical_agent():
    print_header("CLINICAL AGENT TESTS")

    passed = 0
    failed = 0

    for i, test in enumerate(TEST_CASES, 1):
        print(f"\n{BOLD}  Test {i}: {test['name']}{RESET}")
        print_info(f"Findings: {test['clinical_input']['radiology_findings'][:60]}...")

        try:
            response = requests.post(
                f"{BASE_URL}/clinical-agent",
                json=test["clinical_input"],
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                # Validate response fields
                assert "differential_diagnosis" in data, "Missing differential_diagnosis"
                assert "reasoning" in data, "Missing reasoning"
                assert "confidence" in data, "Missing confidence"
                assert "urgency" in data, "Missing urgency"
                assert "recommended_followup" in data, "Missing recommended_followup"
                assert len(data["differential_diagnosis"]) > 0, "Empty diagnosis list"
                assert data["urgency"] in ["routine", "urgent", "emergency"], f"Invalid urgency: {data['urgency']}"

                print_pass(f"Status 200 OK")
                print_result("Diagnosis", ", ".join(data["differential_diagnosis"]))
                print_result("Urgency", data["urgency"])
                print_result("Confidence", data["confidence"])
                print_result("Case ID", data["case_id"])
                passed += 1

            else:
                print_fail(f"Status {response.status_code}: {response.text[:100]}")
                failed += 1

        except AssertionError as e:
            print_fail(f"Validation error: {e}")
            failed += 1
        except requests.exceptions.ConnectionError:
            print_fail("Cannot connect to API — is the server running?")
            failed += 1
            break
        except Exception as e:
            print_fail(f"Unexpected error: {e}")
            failed += 1

    # Summary
    print(f"\n{BOLD}  Clinical Agent Results: {GREEN}{passed} passed{RESET} | {RED}{failed} failed{RESET}")
    return passed, failed


# ── Evidence Agent Tests ─────────────────────────────────
def test_evidence_agent():
    print_header("EVIDENCE AGENT TESTS")

    passed = 0
    failed = 0

    evidence_cases = [
        {
            "name": "Pneumonia evidence search",
            "input": {
                "case_id": f"TEST_EV_PNEUMONIA_{datetime.now().strftime('%H%M%S')}",
                "patient_code": "TEST_001",
                "diagnosis": ["Pneumonia", "Pulmonary Edema", "Atelectasis"],
                "radiology_findings": "Increased opacity in right lower lobe. Possible consolidation."
            }
        },
        {
            "name": "Pneumothorax evidence search",
            "input": {
                "case_id": f"TEST_EV_PNEUMO_{datetime.now().strftime('%H%M%S')}",
                "patient_code": "TEST_002",
                "diagnosis": ["Pneumothorax", "Tension Pneumothorax"],
                "radiology_findings": "Large air collection in left pleural space. Mediastinal shift."
            }
        },
        {
            "name": "Normal findings evidence",
            "input": {
                "case_id": f"TEST_EV_NORMAL_{datetime.now().strftime('%H%M%S')}",
                "patient_code": "TEST_003",
                "diagnosis": ["Normal chest X-ray"],
                "radiology_findings": "No acute cardiopulmonary findings. Clear lung fields."
            }
        }
    ]

    for i, test in enumerate(evidence_cases, 1):
        print(f"\n{BOLD}  Test {i}: {test['name']}{RESET}")
        print_info(f"Diagnosis: {', '.join(test['input']['diagnosis'])}")

        try:
            response = requests.post(
                f"{BASE_URL}/evidence-agent",
                json=test["input"],
                timeout=60  # longer timeout for PubMed search
            )

            if response.status_code == 200:
                data = response.json()

                # Validate response fields
                assert "search_keywords" in data, "Missing search_keywords"
                assert "evidence_summary" in data, "Missing evidence_summary"
                assert "citations" in data, "Missing citations"
                assert "total_papers_found" in data, "Missing total_papers_found"
                assert len(data["evidence_summary"]) > 20, "Evidence summary too short"

                print_pass(f"Status 200 OK")
                print_result("Keywords", data["search_keywords"])
                print_result("Papers found", data["total_papers_found"])
                print_result("Summary preview", data["evidence_summary"][:80] + "...")

                if data["citations"]:
                    print_result("First citation", data["citations"][0]["title"][:60] + "...")
                    print_result("PubMed URL", data["citations"][0]["url"])

                passed += 1

            else:
                print_fail(f"Status {response.status_code}: {response.text[:100]}")
                failed += 1

        except AssertionError as e:
            print_fail(f"Validation error: {e}")
            failed += 1
        except requests.exceptions.ConnectionError:
            print_fail("Cannot connect to API — is the server running?")
            failed += 1
            break
        except Exception as e:
            print_fail(f"Unexpected error: {e}")
            failed += 1

    # Summary
    print(f"\n{BOLD}  Evidence Agent Results: {GREEN}{passed} passed{RESET} | {RED}{failed} failed{RESET}")
    return passed, failed


# ── Health Check ─────────────────────────────────────────
def test_health():
    print_header("HEALTH CHECK")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_pass("API is running")
            return True
        else:
            print_fail(f"Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_fail("API is not running — start it with: python start_api.py")
        return False


# ── Main ─────────────────────────────────────────────────
if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "both"

    print(f"\n{BOLD}{'='*60}")
    print(f"  RADIOLOGY AI — AGENT TEST SUITE")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Target: {BASE_URL}")
    print(f"{'='*60}{RESET}")

    # Always check health first
    if not test_health():
        print(f"\n{RED}Stopping tests — API is not running.{RESET}")
        sys.exit(1)

    total_passed = 0
    total_failed = 0

    if arg in ("clinical", "both"):
        p, f = test_clinical_agent()
        total_passed += p
        total_failed += f

    if arg in ("evidence", "both"):
        p, f = test_evidence_agent()
        total_passed += p
        total_failed += f

    # Final summary
    print_header("FINAL SUMMARY")
    print(f"  {BOLD}Total Passed: {GREEN}{total_passed}{RESET}")
    print(f"  {BOLD}Total Failed: {RED}{total_failed}{RESET}")

    if total_failed == 0:
        print(f"\n  {GREEN}{BOLD}🎉 All tests passed!{RESET}\n")
    else:
        print(f"\n  {YELLOW}{BOLD}⚠️  Some tests failed — check errors above.{RESET}\n")

    sys.exit(0 if total_failed == 0 else 1)