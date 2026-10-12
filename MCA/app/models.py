"""
SQLAlchemy Database Models for Smart Crop Doctor
Defines: User, Disease, Treatment, and ScanLog tables
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    phone_number = Column(String(15), unique=True, nullable=True, index=True)
    name = Column(String(100), nullable=True)
    role = Column(String(20), default="farmer")       # 'farmer' or 'admin'
    preferred_lang = Column(String(5), default="mr")   # 'mr', 'hi', or 'en'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    scan_logs = relationship("ScanLog", back_populates="user")


class Disease(Base):
    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    crop_name = Column(String(50), nullable=False, index=True) # Pomegranate, Onion, Tomato
    model_class_name = Column(String(100), unique=True, nullable=False, index=True)
    common_name_en = Column(String(100), nullable=False)
    common_name_mr = Column(String(100), nullable=False)
    common_name_hi = Column(String(100), nullable=False)
    is_healthy = Column(Boolean, default=False)
    symptoms_en = Column(Text, nullable=True)
    symptoms_mr = Column(Text, nullable=True)
    symptoms_hi = Column(Text, nullable=True)

    # Relationships
    treatment = relationship("Treatment", back_populates="disease", uselist=False)


class Treatment(Base):
    __tablename__ = "treatments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=False, unique=True)
    
    # Organic remedies (stored per language)
    organic_mr = Column(Text, nullable=False)
    organic_hi = Column(Text, nullable=False)
    organic_en = Column(Text, nullable=False)

    # Chemical remedies with dosage
    chemical_mr = Column(Text, nullable=False)
    chemical_hi = Column(Text, nullable=False)
    chemical_en = Column(Text, nullable=False)

    # Preventive farming practices
    preventive_mr = Column(Text, nullable=False)
    preventive_hi = Column(Text, nullable=False)
    preventive_en = Column(Text, nullable=False)

    # Agriculture officer disclaimer note
    officer_note_mr = Column(
        Text, 
        default="अधिक माहितीसाठी जवळच्या कृषी विज्ञान केंद्र (KVK) किंवा तालुका कृषी अधिकाऱ्यांशी संपर्क साधा."
    )
    officer_note_hi = Column(
        Text, 
        default="सटीक सलाह और उचित कीटनाशक मात्रा के लिए स्थानीय कृषि अधिकारी से संपर्क करें।"
    )
    officer_note_en = Column(
        Text, 
        default="Consult your local Agriculture Extension Officer or Krishi Vigyan Kendra for dosage verification."
    )

    # Relationships
    disease = relationship("Disease", back_populates="treatment")


class ScanLog(Base):
    __tablename__ = "scan_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    image_path = Column(String(255), nullable=False)
    crop_detected = Column(String(50), nullable=False)
    predicted_class = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    is_low_confidence = Column(Boolean, default=False)
    scanned_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="scan_logs")
