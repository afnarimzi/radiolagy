"""
Test LangGraph Pipeline
Run: python test_langgraph.py
"""
from app.pipeline.langgraph_pipeline import run_pipeline
import os

if __name__ == "__main__":
    test_images = [
        "test_images/p10004457.jpeg",
        "test_images/p10005858.jpeg"
    ]

    image = next((p for p in test_images if os.path.exists(p)), None)

    if not image:
        print("❌ No test image found in test_images/")
    else:
        result = run_pipeline(
            image_path=image,
            patient_code="LANGGRAPH_TEST_001"
        )
        print("\n✅ LangGraph pipeline test complete!")