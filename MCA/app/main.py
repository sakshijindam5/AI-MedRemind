"""
FastAPI Backend Application - Smart Crop Disease Detector
Serves:
  - POST /api/predict (Leaf verification, MobileNetV2 top-3, multilingual treatment, audio)
  - GET  /api/treatment/{disease_id} (Multilingual advice details)
  - GET  /api/history (Farmer scan history)
  - GET  /api/analytics (Scans per week, most detected diseases)
  - HTML views for farmer mobile app, history, and admin
"""

import os
import uuid
import io
from pathlib import Path
from typing import Optional
from datetime import datetime

from PIL import Image
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

# Internal modules
from app.database import engine, Base, get_db, SessionLocal
from app.models import User, Disease, Treatment, ScanLog
from app.schemas import PredictionResponse, SinglePrediction, TreatmentDetail
from app.ml.model import model_engine
from app.ml.validator import is_valid_leaf_image
from app.services.disease_service import seed_database_diseases, get_disease_info_and_treatment
from app.services.audio_service import generate_treatment_audio

# Paths
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
TEMPLATES_DIR = BASE_DIR / "templates"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Initialize FastAPI App
app = FastAPI(
    title="Smart Crop Disease Detector",
    description="Multilingual (Marathi, Hindi, English) Crop Doctor API with PyTorch MobileNetV2",
    version="1.0.0"
)

# CORS Middleware (allows mobile and external frontends to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Assets & Uploads
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ---------------------------------------------------------------------------
# Startup Event: Initialize Database & Seed Treatments
# ---------------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    # Automatically create SQLite tables if they do not exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database_diseases(db)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 1. Prediction Endpoint
# ---------------------------------------------------------------------------
@app.post("/api/predict", response_model=PredictionResponse)
async def predict_crop_disease(
    file: UploadFile = File(...),
    lang: str = Form("mr"),                  # 'mr' (Marathi), 'hi' (Hindi), 'en' (English)
    user_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Main prediction pipeline:
    1. Validates that the uploaded image contains plant foliage (rejects non-leaf images).
    2. Runs PyTorch MobileNetV2 inference and computes top-3 disease probabilities.
    3. Enforces confidence cutoff (70%): requests clearer photo if confidence is low.
    4. Retrieves verified agronomic treatments in Marathi, Hindi, or English.
    5. Generates voice audio via gTTS.
    6. Logs the scan into the database for history and analytics.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image (JPEG, PNG).")

    # Read image into memory
    contents = await file.read()
    try:
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or unreadable image file.")

    # 1. Non-Leaf Image Validation Check (Feature 1)
    is_leaf, leaf_msg = is_valid_leaf_image(pil_image)
    if not is_leaf:
        # Localized warning message
        rejection_msgs = {
            "mr": "कृपया पिकाच्या पानाचा स्पष्ट फोटो काढा. (पाने ओळखता आली नाहीत).",
            "hi": "कृपया फसल की पत्ती का स्पष्ट फोटो लें। (पत्ती की पहचान नहीं हो सकी)।",
            "en": leaf_msg
        }
        return PredictionResponse(
            success=False,
            message=rejection_msgs.get(lang, leaf_msg),
            leaf_check_passed=False,
            is_low_confidence=True,
            top_predictions=[],
            selected_language=lang,
            treatment=None,
            audio_url=None,
            image_url=None
        )

    # 2. Save Uploaded Image to disk for history display
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    save_path = UPLOADS_DIR / filename
    pil_image.save(save_path, format="JPEG", quality=85)
    image_web_url = f"/static/uploads/{filename}"

    # 3. PyTorch Model Inference (Top-3 Predictions)
    raw_predictions = model_engine.predict(pil_image, top_k=3)
    
    top_pred = raw_predictions[0]
    top_class_name = top_pred["class_name"]
    confidence_score = top_pred["confidence"]
    is_low_conf = confidence_score < 0.70  # 70% threshold (Feature 3)

    # Build formatted top predictions with localized names
    formatted_top = []
    for pred in raw_predictions:
        disease_info = get_disease_info_and_treatment(db, pred["class_name"], lang=lang)
        common_name = disease_info["disease_name"] if disease_info else pred["class_name"]
        
        formatted_top.append(SinglePrediction(
            rank=pred["rank"],
            class_name=pred["class_name"],
            crop_name=pred["crop_name"],
            common_name=common_name,
            confidence=round(pred["confidence"], 4),
            confidence_percentage=pred["confidence_percentage"],
            is_healthy=pred["is_healthy"]
        ))

    # 4. Save to Database Scan History
    scan_log = ScanLog(
        user_id=user_id,
        image_path=image_web_url,
        crop_detected=top_pred["crop_name"],
        predicted_class=top_class_name,
        confidence=confidence_score,
        is_low_confidence=is_low_conf
    )
    db.add(scan_log)
    db.commit()
    db.refresh(scan_log)

    # 5. Low-Confidence Handling (Feature 3)
    if is_low_conf:
        low_conf_msgs = {
            "mr": "अंदाज अचूक नाही (विश्वासार्हता ७०% पेक्षा कमी). कृपया पानाचा जवळून, चांगल्या उजेडात दुसरा फोटो काढा.",
            "hi": "सटीक परिणाम नहीं मिल सका (सटीकता 70% से कम)। कृपया अच्छी रोशनी में पत्ती का नया फोटो लें।",
            "en": "Confidence is below 70%. Please take a clearer photo in good lighting instead of guessing."
        }
        return PredictionResponse(
            success=True,
            message=low_conf_msgs.get(lang, low_conf_msgs["en"]),
            leaf_check_passed=True,
            is_low_confidence=True,
            top_predictions=formatted_top,
            selected_language=lang,
            treatment=None,
            audio_url=None,
            image_url=image_web_url
        )

    # 6. High-Confidence Treatment Retrieval & Audio Generation
    treatment_data = get_disease_info_and_treatment(db, top_class_name, lang=lang)
    treatment_detail = None
    audio_url = None

    if treatment_data:
        treatment_detail = TreatmentDetail(**treatment_data)

        # Prepare summary sentence for Voice Output (Audio)
        if treatment_data["is_healthy"]:
            voice_text = {
                "mr": f"{treatment_data['crop_name']} पीक निरोगी आहे. कोणत्याही औषधाची गरज नाही.",
                "hi": f"{treatment_data['crop_name']} की फसल पूरी तरह स्वस्थ है। किसी कीटनाशक की जरूरत नहीं है।",
                "en": f"The {treatment_data['crop_name']} crop is healthy. No pesticide required."
            }.get(lang, "Crop is healthy.")
        else:
            voice_text = {
                "mr": f"{treatment_data['crop_name']} वर {treatment_data['disease_name']} आढळला आहे. सेंद्रिय उपाय: {treatment_data['organic']} रासायनिक उपाय: {treatment_data['chemical']}",
                "hi": f"{treatment_data['crop_name']} में {treatment_data['disease_name']} पाया गया है। जैविक उपचार: {treatment_data['organic']} रासायनिक उपचार: {treatment_data['chemical']}",
                "en": f"Detected {treatment_data['disease_name']} in {treatment_data['crop_name']}. Organic option: {treatment_data['organic']} Chemical option: {treatment_data['chemical']}"
            }.get(lang, f"Detected {treatment_data['disease_name']}.")

        audio_url = generate_treatment_audio(voice_text, lang=lang)

    success_msgs = {
        "mr": "रोग निदान यशस्वी!",
        "hi": "रोग की पहचान सफल!",
        "en": "Disease identified successfully!"
    }

    return PredictionResponse(
        success=True,
        message=success_msgs.get(lang, "Success"),
        leaf_check_passed=True,
        is_low_confidence=False,
        top_predictions=formatted_top,
        selected_language=lang,
        treatment=treatment_detail,
        audio_url=audio_url,
        image_url=image_web_url
    )


# ---------------------------------------------------------------------------
# 2. Treatment Endpoint by Disease ID
# ---------------------------------------------------------------------------
@app.get("/api/treatment/{disease_id}")
def get_treatment_by_id(disease_id: int, lang: str = "mr", db: Session = Depends(get_db)):
    """Fetches full treatment guidelines for a specific disease ID."""
    disease = db.query(Disease).filter(Disease.id == disease_id).first()
    if not disease:
        raise HTTPException(status_code=404, detail="Disease not found.")
    
    treatment_data = get_disease_info_and_treatment(db, disease.model_class_name, lang=lang)
    if not treatment_data:
        raise HTTPException(status_code=404, detail="Treatment data not found.")
    
    return treatment_data


# ---------------------------------------------------------------------------
# 3. Farmer Scan History Endpoint (Feature 7)
# ---------------------------------------------------------------------------
@app.get("/api/history")
def get_scan_history(limit: int = 20, lang: str = "mr", db: Session = Depends(get_db)):
    """Returns recent scan history ordered by newest first."""
    logs = db.query(ScanLog).order_by(ScanLog.scanned_at.desc()).limit(limit).all()
    results = []

    for log in logs:
        disease_info = get_disease_info_and_treatment(db, log.predicted_class, lang=lang)
        d_name = disease_info["disease_name"] if disease_info else log.predicted_class

        results.append({
            "id": log.id,
            "image_url": log.image_path,
            "crop_detected": log.crop_detected,
            "predicted_class": log.predicted_class,
            "disease_name": d_name,
            "confidence": round(log.confidence, 4),
            "confidence_percentage": f"{log.confidence * 100:.1f}%",
            "is_low_confidence": log.is_low_confidence,
            "scanned_at": log.scanned_at.strftime("%d %b %Y, %I:%M %p")
        })

    return results


# ---------------------------------------------------------------------------
# 4. Analytics Dashboard Endpoint (Feature 9)
# ---------------------------------------------------------------------------
@app.get("/api/analytics")
def get_analytics(db: Session = Depends(get_db)):
    """
    Returns high-level statistics for viva and admin dashboard:
    - Total scans
    - Scans per crop
    - Top 5 most detected diseases
    """
    total_scans = db.query(ScanLog).count()
    low_conf_count = db.query(ScanLog).filter(ScanLog.is_low_confidence == True).count()

    # Most detected diseases
    top_diseases = db.query(
        ScanLog.predicted_class,
        func.count(ScanLog.id).label("count")
    ).group_by(ScanLog.predicted_class).order_by(func.count(ScanLog.id).desc()).limit(5).all()

    # Scans per crop
    crop_counts = db.query(
        ScanLog.crop_detected,
        func.count(ScanLog.id).label("count")
    ).group_by(ScanLog.crop_detected).all()

    return {
        "total_scans": total_scans,
        "low_confidence_scans": low_conf_count,
        "scans_by_crop": {crop: count for crop, count in crop_counts},
        "most_detected_diseases": [
            {"disease": d, "count": c} for d, c in top_diseases
        ]
    }


# ---------------------------------------------------------------------------
# 5. HTML Frontend Views
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index_view(request: Request):
    """Main mobile-first interface for farmers."""
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/history", response_class=HTMLResponse)
def history_view(request: Request):
    """Farmer scan history page."""
    return templates.TemplateResponse(request=request, name="history.html")

@app.get("/admin", response_class=HTMLResponse)
def admin_view(request: Request):
    """Admin and analytics dashboard."""
    return templates.TemplateResponse(request=request, name="admin.html")
