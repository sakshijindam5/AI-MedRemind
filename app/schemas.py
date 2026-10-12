"""
Pydantic Schemas for Request & Response Data Validation
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class SinglePrediction(BaseModel):
    rank: int
    class_name: str
    crop_name: str
    common_name: str
    confidence: float
    confidence_percentage: str
    is_healthy: bool

class TreatmentDetail(BaseModel):
    disease_id: int
    crop_name: str
    disease_name: str
    is_healthy: bool
    organic: str
    chemical: str
    preventive: str
    officer_note: str

class PredictionResponse(BaseModel):
    success: bool
    message: str
    leaf_check_passed: bool
    is_low_confidence: bool
    top_predictions: List[SinglePrediction]
    selected_language: str
    treatment: Optional[TreatmentDetail] = None
    audio_url: Optional[str] = None
    image_url: Optional[str] = None

class ScanHistoryItem(BaseModel):
    id: int
    image_url: str
    crop_detected: str
    disease_name: str
    confidence: float
    confidence_percentage: str
    is_low_confidence: bool
    scanned_at: str

    class Config:
        from_attributes = True

class AnalyticsResponse(BaseModel):
    total_scans: int
    low_confidence_scans: int
    most_detected_diseases: List[dict]
    scans_by_crop: dict
