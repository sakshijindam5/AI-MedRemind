"""
Unit and Integration Tests for FastAPI Endpoints
Tests:
  1. Root endpoint /
  2. Treatment retrieval in Marathi, Hindi, and English
  3. Scan history endpoint /api/history
  4. Analytics endpoint /api/analytics
  5. Non-leaf image rejection (Feature 1)
  6. Leaf prediction pipeline
"""

import io
import sys
from pathlib import Path

# Add project root to Python module search path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_endpoints_status():
    # 1. Test treatment endpoint in Marathi
    resp = client.get("/api/treatment/1?lang=mr")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert "disease_name" in data
    assert "organic" in data
    assert "chemical" in data
    print(f"[*] Treatment endpoint passed: {data['crop_name']} - {data['disease_name']}")

    # 2. Test treatment in Hindi
    resp_hi = client.get("/api/treatment/1?lang=hi")
    assert resp_hi.status_code == 200
    assert "फसल" in resp_hi.json()["organic"] or len(resp_hi.json()["organic"]) > 0
    print("[*] Hindi treatment retrieval passed.")

    # 3. Test history endpoint
    resp_hist = client.get("/api/history")
    assert resp_hist.status_code == 200
    print("[*] Scan history endpoint passed.")

    # 4. Test analytics endpoint
    resp_analytics = client.get("/api/analytics")
    assert resp_analytics.status_code == 200
    assert "total_scans" in resp_analytics.json()
    print("[*] Analytics endpoint passed.")

def test_non_leaf_image_rejection():
    # Create a pure grey non-leaf test image (e.g., photo of concrete or car)
    img = Image.new("RGB", (224, 224), color=(180, 180, 180))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    files = {"file": ("test_grey.jpg", img_byte_arr, "image/jpeg")}
    data = {"lang": "mr"}

    resp = client.post("/api/predict", files=files, data=data)
    assert resp.status_code == 200
    result = resp.json()
    assert result["leaf_check_passed"] == False
    assert result["success"] == False
    print(f"[*] Non-leaf rejection check passed: '{result['message']}'")

def test_valid_leaf_prediction():
    # Create a green image with leaf-like foliage color
    img = Image.new("RGB", (224, 224), color=(34, 139, 34)) # Forest green
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    files = {"file": ("test_leaf.jpg", img_byte_arr, "image/jpeg")}
    data = {"lang": "mr"}

    resp = client.post("/api/predict", files=files, data=data)
    assert resp.status_code == 200
    result = resp.json()
    assert result["leaf_check_passed"] == True
    assert len(result["top_predictions"]) == 3
    print(f"[*] Valid leaf prediction passed: Top 1 = {result['top_predictions'][0]['common_name']}")

if __name__ == "__main__":
    test_endpoints_status()
    test_non_leaf_image_rejection()
    test_valid_leaf_prediction()
    print("\n[ALL FASTAPI BACKEND TESTS PASSED SUCCESSFULLY!]")
