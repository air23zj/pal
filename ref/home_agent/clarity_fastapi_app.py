import os
import concurrent.futures
import json
import traceback
from typing import List, Optional, Dict, Set
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Request, status, WebSocket
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Text, Boolean, or_, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
from typing import Optional, List
import jwt
from passlib.context import CryptContext
from fastapi.requests import Request
import aiohttp
from bs4 import BeautifulSoup
import openai
from openai import AsyncOpenAI
import traceback
from pydantic import BaseModel, EmailStr, Field
from litellm import completion
import google.generativeai as genai
from loguru import logger
import random
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from langchain.text_splitter import RecursiveCharacterTextSplitter
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from urllib.parse import urlparse, parse_qs
import sys
import imghdr
from PIL import Image
import io
import fastapi.responses
import pillow_heif
from fastapi import WebSocketDisconnect
import boto3
from botocore.config import Config
from decimal import Decimal
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import asyncio as aioredis
import tempfile
from functools import lru_cache
from cachetools import TTLCache

# Register HEIF/AVIF opener with Pillow
pillow_heif.register_heif_opener()

# Environment variables and constants from original app
# API keys should be set via environment variables, not hardcoded
# os.environ["OPENAI_API_KEY"] = "your-openai-api-key"
# os.environ["GEMINI_API_KEY"] = "your-gemini-api-key"
# os.environ["SERPER_SEARCH_API_KEY"] = "your-serper-api-key"
# os.environ["GROQ_API_KEY"] = "your-groq-api-key"
# os.environ["NEWS_API_KEY"] = "your-newsapi-key"
# os.environ["SERPAPI_API_KEY"] = "your-serpapi-key"
# os.environ["OPENWEATHER_API_KEY"] = "your-openweather-api-key"

# Configuration
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
if not OPENWEATHER_API_KEY:
    logger.error("OpenWeatherMap API key is not set in environment variables")
    raise ValueError("OpenWeatherMap API key is required")

# Validate API key format
if not isinstance(OPENWEATHER_API_KEY, str) or len(OPENWEATHER_API_KEY) != 32:
    logger.error("Invalid OpenWeatherMap API key format")
    raise ValueError("Invalid OpenWeatherMap API key format")

WEATHER_API_BASE_URL = "http://api.openweathermap.org/data/2.5"
SERVER_HOST = "http://localhost:8000"

# Initialize caches
weather_cache = TTLCache(maxsize=100, ttl=600)  # Cache weather data for 10 minutes

# Sample questions
_questions_list = [
    "Who said 'live long and prosper'?",
    "ETFs to invest in AI",
    "Best TV shows Nov 2024",
    "is batman a cop",
    "Is Dune just a cheap ripoff of Star Wars",
    "Healthiest cooking oils",
    "Tax savings ideas",
    "The theory of mind tests",
    "Best age to get pregnant",
    "Can Air China business class passengers use any lounges at SFO?",
    "Is Groq API free?"
]

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./clarity.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
Base = declarative_base()

# Database Models
class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    documents = relationship("DocumentModel", back_populates="owner")
    folders = relationship("FolderModel", back_populates="owner")
    files = relationship("FileModel", back_populates="owner")
    rooms = relationship("RoomModel", back_populates="owner")
    voice_memos = relationship("VoiceMemoModel", back_populates="owner")
    weight_records = relationship("WeightRecordModel", back_populates="owner")
    doctor_visits = relationship("DoctorVisitModel", back_populates="owner")
    exercise_goals = relationship("ExerciseGoalsModel", back_populates="owner", uselist=False)
    dietary_goals = relationship("DietaryGoalsModel", back_populates="owner", uselist=False)
    height_records = relationship("HeightRecordModel", back_populates="owner")
    heart_rate_records = relationship("HeartRateRecordModel", back_populates="owner")
    blood_pressure_records = relationship("BloodPressureRecordModel", back_populates="owner")
    trips = relationship("TripModel", back_populates="owner")
    weather_locations = relationship("WeatherLocationModel", back_populates="owner")

class DocumentModel(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    folder_id = Column(Integer, ForeignKey("folders.id", ondelete="SET NULL"), nullable=True)
    owner = relationship("UserModel", back_populates="documents")
    folder = relationship("FolderModel", back_populates="documents")
    shared_with = relationship("DocumentShareModel", back_populates="document", cascade="all, delete-orphan")

class FolderModel(Base):
    __tablename__ = "folders"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("UserModel", back_populates="folders")
    documents = relationship("DocumentModel", back_populates="folder")

class DocumentShareModel(Base):
    __tablename__ = "document_shares"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))
    shared_with_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    document = relationship("DocumentModel", back_populates="shared_with")

class FileModel(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    path = Column(String)
    size = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("UserModel", back_populates="files")
    shared_with = relationship("FileShareModel", back_populates="file", cascade="all, delete-orphan")

class FileShareModel(Base):
    __tablename__ = "file_shares"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"))
    shared_with_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    file = relationship("FileModel", back_populates="shared_with")

class RoomModel(Base):
    __tablename__ = "rooms"
    id = Column(String, primary_key=True)
    name = Column(String, index=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("UserModel", back_populates="rooms")

class DealModel(Base):
    __tablename__ = "deals"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    image_url = Column(String)
    summary = Column(Text)
    price = Column(String)
    url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Deal(BaseModel):
    id: int
    title: str
    image_url: str
    summary: str
    price: str
    url: str
    created_at: datetime

    class Config:
        from_attributes = True

class VoiceMemoModel(Base):
    __tablename__ = "voice_memos"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    path = Column(String)
    duration = Column(String)
    transcription = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("UserModel", back_populates="voice_memos")

class WeightRecordModel(Base):
    __tablename__ = "weight_records"
    id = Column(Integer, primary_key=True, index=True)
    weight = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("UserModel", back_populates="weight_records")

class DoctorVisitModel(Base):
    __tablename__ = "doctor_visits"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime)
    doctor_name = Column(String)
    reason = Column(String)
    notes = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("UserModel", back_populates="doctor_visits")

class ExerciseGoalsModel(Base):
    __tablename__ = "exercise_goals"
    id = Column(Integer, primary_key=True, index=True)
    daily_steps = Column(Integer)
    weekly_exercise_minutes = Column(Integer)
    owner_id = Column(Integer, ForeignKey("users.id"), unique=True)
    owner = relationship("UserModel", back_populates="exercise_goals")

class DietaryGoalsModel(Base):
    __tablename__ = "dietary_goals"
    id = Column(Integer, primary_key=True, index=True)
    daily_calories = Column(Integer)
    water_intake = Column(Float)
    owner_id = Column(Integer, ForeignKey("users.id"), unique=True)
    owner = relationship("UserModel", back_populates="dietary_goals")

class HeightRecordModel(Base):
    __tablename__ = "height_records"
    id = Column(Integer, primary_key=True, index=True)
    height = Column(Float)  # in centimeters
    date = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("UserModel", back_populates="height_records")

class HeartRateRecordModel(Base):
    __tablename__ = "heart_rate_records"
    id = Column(Integer, primary_key=True, index=True)
    heart_rate = Column(Integer)  # beats per minute
    date = Column(DateTime, default=datetime.utcnow)
    activity_state = Column(String)  # e.g., "resting", "active", "post-exercise"
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("UserModel", back_populates="heart_rate_records")

class BloodPressureRecordModel(Base):
    __tablename__ = "blood_pressure_records"
    id = Column(Integer, primary_key=True, index=True)
    systolic = Column(Integer)  # mmHg
    diastolic = Column(Integer)  # mmHg
    date = Column(DateTime, default=datetime.utcnow)
    notes = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("UserModel", back_populates="blood_pressure_records")

# Add new travel-related models after existing models
class TripModel(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    destination = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("UserModel", back_populates="trips")
    accommodations = relationship("AccommodationModel", back_populates="trip", cascade="all, delete-orphan")
    flights = relationship("FlightModel", back_populates="trip", cascade="all, delete-orphan")
    car_rentals = relationship("CarRentalModel", back_populates="trip", cascade="all, delete-orphan")

class AccommodationModel(Base):
    __tablename__ = "accommodations"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)  # hotel, airbnb, etc.
    name = Column(String)
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    location = Column(String)
    price = Column(Float)
    booking_reference = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    trip = relationship("TripModel", back_populates="accommodations")

class FlightModel(Base):
    __tablename__ = "flights"
    id = Column(Integer, primary_key=True, index=True)
    airline = Column(String)
    flight_number = Column(String)
    departure_airport = Column(String)
    arrival_airport = Column(String)
    departure_time = Column(DateTime)
    arrival_time = Column(DateTime)
    price = Column(Float)
    booking_reference = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    trip = relationship("TripModel", back_populates="flights")

class CarRentalModel(Base):
    __tablename__ = "car_rentals"
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String)
    car_type = Column(String)
    pickup_location = Column(String)
    dropoff_location = Column(String)
    pickup_time = Column(DateTime)
    dropoff_time = Column(DateTime)
    price = Column(Float)
    booking_reference = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    trip = relationship("TripModel", back_populates="car_rentals")

class WeatherLocationBase(BaseModel):
    name: str

class WeatherLocationCreate(WeatherLocationBase):
    pass

class WeatherLocation(WeatherLocationBase):
    id: int
    owner_id: int
    current_temp: Optional[float] = None

    class Config:
        from_attributes = True

class WeatherLocationModel(Base):
    __tablename__ = "weather_locations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    current_temp = Column(Float, nullable=True)
    last_updated = Column(DateTime, nullable=True)
    owner = relationship("UserModel", back_populates="weather_locations")

# Create database tables
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Security
SECRET_KEY = "your-secret-key"  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic Models
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class DocumentShare(BaseModel):
    username: str
    can_edit: bool = False

class SearchRequest(BaseModel):
    query: str
    search_engine: Optional[str] = "serper"

class QuestionRequest(BaseModel):
    query: str
    contexts: List[dict]

class YouTubeRequest(BaseModel):
    url: str

class DocumentBase(BaseModel):
    title: str
    content: str
    folder_id: Optional[int] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(DocumentBase):
    title: Optional[str] = None
    content: Optional[str] = None
    folder_id: Optional[int] = None

class Document(DocumentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    owner_id: int

    class Config:
        from_attributes = True

class FolderBase(BaseModel):
    name: str

class FolderCreate(FolderBase):
    pass

class Folder(FolderBase):
    id: int
    created_at: datetime
    owner_id: int
    documents: List[Document] = []
    
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    
    class Config:
        from_attributes = True

class FileBase(BaseModel):
    name: str
    size: int

class FileResponse(BaseModel):
    id: int
    name: str
    size: int
    created_at: datetime
    owner_id: int
    url: str

    class Config:
        from_attributes = True

class Room(BaseModel):
    id: str
    name: str
    created_by: str
    created_at: datetime
    participants: List[str] = []

class RoomCreate(BaseModel):
    room_name: str

class NewsArticle(BaseModel):
    id: str
    title: str
    url: str
    image_url: str | None = None
    summary: str | None = None

class VoiceMemo(BaseModel):
    id: int
    filename: str
    duration: str
    transcription: Optional[str]
    summary: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class WeightRecord(BaseModel):
    id: int
    weight: float
    date: datetime
    owner_id: int

    class Config:
        from_attributes = True

class DoctorVisitBase(BaseModel):
    date: Optional[datetime] = None
    doctor_name: str = Field(alias="doctorName")
    reason: str
    notes: str

    class Config:
        from_attributes = True
        populate_by_name = True
        allow_population_by_field_name = True

class DoctorVisitCreate(DoctorVisitBase):
    pass

class DoctorVisit(DoctorVisitBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True
        populate_by_name = True
        allow_population_by_field_name = True

class ExerciseGoalsBase(BaseModel):
    daily_steps: int = Field(alias="dailySteps")
    weekly_exercise_minutes: int = Field(alias="weeklyExerciseMinutes")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

class ExerciseGoalsCreate(ExerciseGoalsBase):
    pass

class ExerciseGoals(ExerciseGoalsBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True
        populate_by_name = True
        allow_population_by_field_name = True

class DietaryGoalsBase(BaseModel):
    daily_calories: int = Field(alias="dailyCalories")
    water_intake: float = Field(alias="waterIntake")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

class DietaryGoalsCreate(DietaryGoalsBase):
    pass

class DietaryGoals(DietaryGoalsBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True
        populate_by_name = True
        allow_population_by_field_name = True

class WeightRecordBase(BaseModel):
    weight: float
    date: Optional[datetime] = None

class WeightRecordCreate(WeightRecordBase):
    pass

class WeightRecord(WeightRecordBase):
    id: int
    owner_id: int
    
    class Config:
        from_attributes = True

class HeightRecordBase(BaseModel):
    height: float
    date: Optional[datetime] = None

class HeightRecordCreate(HeightRecordBase):
    pass

class HeightRecord(HeightRecordBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class HeartRateRecordBase(BaseModel):
    heart_rate: int
    activity_state: str
    date: Optional[datetime] = None

    class Config:
        from_attributes = True

class HeartRateRecordCreate(HeartRateRecordBase):
    pass

class HeartRateRecord(HeartRateRecordBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class BloodPressureRecordBase(BaseModel):
    systolic: int
    diastolic: int
    date: Optional[datetime] = None
    notes: Optional[str] = None

class BloodPressureRecordCreate(BloodPressureRecordBase):
    pass

class BloodPressureRecord(BloodPressureRecordBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

# Add Pydantic models for request/response
class TripBase(BaseModel):
    title: str
    destination: str
    start_date: datetime
    end_date: datetime
    notes: Optional[str] = None

class TripCreate(TripBase):
    pass

class Trip(TripBase):
    id: int
    created_at: datetime
    owner_id: int

    class Config:
        from_attributes = True

class AccommodationBase(BaseModel):
    type: str = Field(description="Type of accommodation (hotel, airbnb, etc.)")
    name: str
    check_in: datetime
    check_out: datetime
    location: str
    price: float
    booking_reference: Optional[str] = None
    notes: Optional[str] = None

class AccommodationCreate(AccommodationBase):
    trip_id: int

class Accommodation(AccommodationBase):
    id: int
    trip_id: int

    class Config:
        from_attributes = True

class FlightBase(BaseModel):
    airline: str
    flight_number: str
    departure_airport: str
    arrival_airport: str
    departure_time: datetime
    arrival_time: datetime
    price: float
    booking_reference: Optional[str] = None
    notes: Optional[str] = None

class FlightCreate(FlightBase):
    trip_id: int

class Flight(FlightBase):
    id: int
    trip_id: int

    class Config:
        from_attributes = True

class CarRentalBase(BaseModel):
    company: str
    car_type: str
    pickup_location: str
    dropoff_location: str
    pickup_time: datetime
    dropoff_time: datetime
    price: float
    booking_reference: Optional[str] = None
    notes: Optional[str] = None

class CarRentalCreate(CarRentalBase):
    trip_id: int

class CarRental(CarRentalBase):
    id: int
    trip_id: int

    class Config:
        from_attributes = True

# Security Functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    logger.debug(f"Authenticating user with token: {token[:10]}...")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        logger.debug("Decoding JWT token...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        logger.debug(f"Token decoded, username: {username}")
        if username is None:
            logger.error("No username found in token")
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {str(e)}")
        raise credentials_exception

    logger.debug(f"Looking up user in database: {username}")
    user = db.query(UserModel).filter(UserModel.username == token_data.username).first()
    if user is None:
        logger.error(f"User not found in database: {username}")
        raise credentials_exception
    logger.debug(f"User found: {user.username}")
    return user

# Helper functions (preserved from original app)
async def search_with_serper(query: str, subscription_key: str):
    try:
        headers = {
            'X-API-KEY': subscription_key,
            'Content-Type': 'application/json'
        }
        payload = {
            'q': query
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post('https://google.serper.dev/search', headers=headers, json=payload) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="Search API request failed")
                
                data = await response.json()
                logger.info(f"Search API response data: {data}")
                
                contexts = []
                if 'organic' in data:
                    for item in data['organic']:
                        # Log each item before processing
                        logger.info(f"Raw search result item: {item}")
                        
                        # Get values with detailed logging
                        title = item.get('title')
                        link = item.get('link')
                        snippet = item.get('snippet')
                        
                        logger.info(f"Extracted values - Title: {title}, Link: {link}, Snippet: {snippet}")
                        
                        context = {
                            'title': title if title else '',
                            'link': link if link else '',
                            'snippet': snippet if snippet else ''
                        }
                        
                        # Log the processed context
                        logger.info(f"Processed context: {context}")
                        
                        if link:  # Only require link to be present
                            contexts.append(context)
                
                # Log final results
                logger.info(f"Final search results: {contexts}")
                return contexts[:5]
    except Exception as e:
        logger.error(f"Error in search_with_serper: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_search_sum(query: str, contexts: List[dict]) -> str:
    """Get a summary of search results with citations"""
    try:
        # Format contexts with citation numbers
        formatted_contexts = []
        for i, ctx in enumerate(contexts, 1):
            formatted_contexts.append(f"{ctx['snippet']} [Citation: {i}]")
        
        context_text = "\n\n".join(formatted_contexts)
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant that provides accurate information with citations. Always cite your sources using [X] format where X is the citation number."},
            {"role": "user", "content": f"Based on the following sources, answer this question: {query}\n\nSources:\n{context_text}"}
        ]
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Error in get_search_sum: {str(e)}")
        raise

async def get_related_questions(query: str, contexts: List[dict]) -> List[str]:
    """Generate related questions based on the search results"""
    try:
        context_text = "\n".join(ctx['snippet'] for ctx in contexts)
        
        messages = [
            {"role": "system", "content": "Generate 3-5 related questions that users might want to ask next. Make them natural and relevant to the original query and search results."},
            {"role": "user", "content": f"Original question: {query}\n\nSearch results:\n{context_text}"}
        ]
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )
        
        # Split the response into individual questions and clean them up
        questions = [
            q.strip().strip('•-*').strip()
            for q in response.choices[0].message.content.strip().split('\n')
            if q.strip() and not q.strip().lower().startswith(('here', 'related', 'questions'))
        ]
        
        return questions[:5]  # Return at most 5 questions
        
    except Exception as e:
        logger.error(f"Error in get_related_questions: {str(e)}")
        return []

async def perform_search(query: str, search_engine: str = "serper") -> dict:
    """
    Perform search using the specified search engine and return formatted results
    """
    try:
        if search_engine == "serper":
            contexts = await search_with_serper(query, os.environ["SERPER_SEARCH_API_KEY"])
            answer = await get_search_sum(query, contexts)
            related = await get_related_questions(query, contexts)
            
            return {
                "answer": answer,
                "sources": [
                    {
                        "title": ctx.get("title", ""),
                        "snippet": ctx.get("snippet", ""),
                        "url": ctx.get("link", "")
                    }
                    for ctx in contexts
                ],
                "related_questions": related
            }
        else:
            raise ValueError(f"Unsupported search engine: {search_engine}")
            
    except Exception as e:
        logger.error(f"Error in perform_search: {str(e)}")
        raise

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.room_participants: Dict[str, Set[str]] = {}
        self.user_to_room: Dict[str, str] = {}  # Track which room each user is in
        self.user_connections: Dict[str, WebSocket] = {}  # Track user's active connection
        self.connection_states: Dict[str, bool] = {}  # Track if connections are being closed
        self.leaving_rooms: Set[str] = set()  # Track users who are in the process of leaving

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
            self.room_participants[room_id] = set()
        self.active_connections[room_id][user_id] = websocket
        self.room_participants[room_id].add(user_id)
        self.user_to_room[user_id] = room_id  # Track user's room
        self.user_connections[user_id] = websocket  # Track user's connection
        self.connection_states[user_id] = True  # Mark connection as active
        logger.info(f"User {user_id} connected to room {room_id}")

    def disconnect(self, room_id: str, user_id: str):
        try:
            # Mark connection as being closed
            self.connection_states[user_id] = False
            
            # If room_id is not provided, try to get it from user_to_room mapping
            if not room_id and user_id in self.user_to_room:
                room_id = self.user_to_room.get(user_id)
                logger.info(f"Retrieved room_id {room_id} for user {user_id} from mapping")

            if room_id and room_id in self.active_connections:
                # Safely remove the connection
                if user_id in self.active_connections[room_id]:
                    del self.active_connections[room_id][user_id]
                    logger.info(f"Removed connection for user {user_id} from room {room_id}")
                
                # Safely remove from participants
                if room_id in self.room_participants:
                    self.room_participants[room_id].discard(user_id)
                    logger.info(f"Removed user {user_id} from room participants {room_id}")
                
                # Clean up empty room
                if not self.active_connections[room_id]:
                    del self.active_connections[room_id]
                    if room_id in self.room_participants:
                        del self.room_participants[room_id]
                    logger.info(f"Removed empty room {room_id}")

            # Always clean up user mappings
            if user_id in self.user_to_room:
                del self.user_to_room[user_id]
                logger.info(f"Removed user {user_id} from user_to_room mapping")
            if user_id in self.user_connections:
                del self.user_connections[user_id]
                logger.info(f"Removed user {user_id} from user_connections mapping")
            if user_id in self.connection_states:
                del self.connection_states[user_id]
                logger.info(f"Removed user {user_id} from connection states")

        except Exception as e:
            logger.error(f"Error in disconnect for room {room_id}, user {user_id}: {str(e)}")

    async def handle_leave_room(self, user_id: str):
        """Handle a user leaving a room, even if room_id is not known"""
        try:
            # Prevent recursive leave room calls
            if user_id in self.leaving_rooms:
                logger.info(f"User {user_id} is already in the process of leaving")
                return

            self.leaving_rooms.add(user_id)
            
            # Get user's current connection
            connection = self.user_connections.get(user_id)
            room_id = self.user_to_room.get(user_id)
            
            logger.info(f"Handling leave room for user {user_id} from room {room_id}")
            
            # Only try to close connection if it's still marked as active
            if connection and self.connection_states.get(user_id, False):
                try:
                    if not connection.client_state.disconnected:
                        await connection.close(code=1000)
                    logger.info(f"Closed connection for user {user_id}")
                except Exception as e:
                    logger.error(f"Error closing connection for user {user_id}: {str(e)}")
            
            # Clean up room if we have a room_id
            if room_id:
                # Notify others before disconnecting
                try:
                    await self.broadcast_to_room(
                        room_id,
                        user_id,
                        {
                            "type": "user-left",
                            "userId": user_id
                        }
                    )
                except Exception as e:
                    logger.error(f"Error broadcasting user left message: {str(e)}")
                
                self.disconnect(room_id, user_id)
            else:
                # If no room_id, just clean up user mappings
                self.disconnect(None, user_id)
                logger.warning(f"No room found for user {user_id} in user_to_room mapping")
                
        except Exception as e:
            logger.error(f"Error handling leave room for user {user_id}: {str(e)}")
            # Ensure user is cleaned up even if there's an error
            try:
                self.disconnect(None, user_id)
            except Exception as cleanup_error:
                logger.error(f"Error in final cleanup for user {user_id}: {str(cleanup_error)}")
        finally:
            # Always remove from leaving_rooms set
            self.leaving_rooms.discard(user_id)

    async def broadcast_to_room(self, room_id: str, sender_id: str, message: dict):
        if room_id not in self.active_connections:
            logger.warning(f"Attempted to broadcast to non-existent room {room_id}")
            return
            
        connections = self.active_connections[room_id].copy()
        for user_id, connection in connections.items():
            if user_id != sender_id:  # Don't send back to sender
                try:
                    if connection and not connection.client_state.disconnected:
                        await connection.send_json(message)
                    else:
                        logger.warning(f"Found stale connection for user {user_id} in room {room_id}")
                        await self.handle_stale_connection(room_id, user_id)
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected while broadcasting to user {user_id} in room {room_id}")
                    await self.handle_stale_connection(room_id, user_id)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id} in room {room_id}: {str(e)}")
                    await self.handle_stale_connection(room_id, user_id)

    async def handle_stale_connection(self, room_id: str, user_id: str):
        """Handle cleanup of stale connections"""
        try:
            if room_id in self.active_connections and user_id in self.active_connections[room_id]:
                connection = self.active_connections[room_id][user_id]
                if connection:
                    try:
                        await connection.close(code=1000)
                    except Exception as e:
                        logger.error(f"Error closing stale connection: {str(e)}")
                self.disconnect(room_id, user_id)
                
                # Notify other participants about the disconnection
                await self.broadcast_to_room(
                    room_id,
                    user_id,
                    {
                        "type": "user-left",
                        "userId": user_id
                    }
                )
        except Exception as e:
            logger.error(f"Error handling stale connection for room {room_id}, user {user_id}: {str(e)}")

    async def close_room(self, room_id: str):
        """Safely close all connections in a room"""
        if room_id in self.active_connections:
            connections = self.active_connections[room_id].copy()
            for user_id, connection in connections.items():
                try:
                    if connection and not connection.client_state.disconnected:
                        await connection.close(code=1000)
                except Exception as e:
                    logger.error(f"Error closing connection for user {user_id} in room {room_id}: {str(e)}")
                self.disconnect(room_id, user_id)
            logger.info(f"Closed all connections in room {room_id}")

# Initialize connection manager
manager = ConnectionManager()

# Add WebSocket exception handler
@app.exception_handler(WebSocketDisconnect)
async def websocket_disconnect_handler(request: Request, exc: WebSocketDisconnect):
    logger.info(f"WebSocket disconnected with code {exc.code}")
    return None

@app.websocket("/ws/room/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str = None,
    db: Session = Depends(get_db)
):
    user = None
    connection_accepted = False
    try:
        logger.info(f"WebSocket connection attempt for room {room_id}")
        
        # Validate room_id
        if not room_id:
            logger.error("No room ID provided")
            await websocket.close(code=1008, reason="No room ID provided")
            return
        
        if not token:
            logger.error("No token provided")
            await websocket.close(code=1008, reason="No token provided")
            return
        
        # Validate token and get user before accepting connection
        try:
            logger.debug(f"Validating token: {token[:10]}...")
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username is None:
                logger.error("Token validation failed: no username in payload")
                await websocket.close(code=1008, reason="Invalid token")
                return
                
            user = db.query(UserModel).filter(UserModel.username == username).first()
            if user is None:
                logger.error(f"User not found: {username}")
                await websocket.close(code=1008, reason="User not found")
                return

            # Check if room exists
            room = db.query(RoomModel).filter(RoomModel.id == room_id).first()
            if not room:
                logger.error(f"Room not found: {room_id}")
                await websocket.close(code=1008, reason="Room not found")
                return

            # Clean up any existing connections for this user
            user_id = str(user.id)
            if user_id in manager.user_connections:
                try:
                    old_connection = manager.user_connections[user_id]
                    if old_connection and not old_connection.client_state.disconnected:
                        await old_connection.close(code=1008, reason="New connection initiated")
                except Exception as e:
                    logger.error(f"Error closing existing connection: {str(e)}")
                finally:
                    await manager.handle_leave_room(user_id)

            logger.info(f"Token validated successfully for user {username}")
            
            # Accept the WebSocket connection
            await websocket.accept()
            connection_accepted = True
            logger.info(f"WebSocket connection accepted for user {username} in room {room_id}")
            
            # Add user to room
            await manager.connect(websocket, room_id, user_id)
            logger.info(f"User {user.username} connected to room {room_id}")
            
            # Notify others that user joined
            await manager.broadcast_to_room(
                room_id,
                user_id,
                {
                    "type": "user-joined",
                    "userId": user_id,
                    "username": user.username
                }
            )
            
            # Handle WebSocket messages
            while True:
                try:
                    message = await websocket.receive_json()
                    logger.debug(f"Received message from user {user.username} in room {room_id}: {message}")
                    
                    # Handle leave room message
                    if message.get("type") == "leave-room":
                        logger.info(f"User {user.username} requested to leave room {room_id}")
                        # Mark connection as being closed before handling leave
                        manager.connection_states[user_id] = False
                        await manager.handle_leave_room(user_id)
                        break
                        
                    await manager.broadcast_to_room(room_id, user_id, message)
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected for user {user.username} in room {room_id}")
                    break
                except json.JSONDecodeError as json_error:
                    logger.error(f"Invalid JSON message received: {str(json_error)}")
                    continue
                except Exception as msg_error:
                    logger.error(f"Error handling message: {str(msg_error)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    continue

        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            if not connection_accepted:
                await websocket.close(code=1008, reason="Token expired")
            return
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            if not connection_accepted:
                await websocket.close(code=1008, reason="Invalid token")
            return
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            if not connection_accepted:
                await websocket.close(code=1008, reason="Authentication failed")
            return
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnect caught in main try-except")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        # Clean up in finally block
        if user:
            user_id = str(user.id)
            # Mark connection as being closed before cleanup
            manager.connection_states[user_id] = False
            await manager.handle_leave_room(user_id)

@app.get("/random_question")
async def get_random_question():
    return {"question": random.choice(_questions_list)}

@app.post("/search")
async def search(request: Request):
    try:
        data = await request.json()
        query = data.get("query")
        search_engine = data.get("search_engine", "serper")  # Default to serper if not specified
        
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")
            
        # Log the incoming request
        logger.info(f"Search request received - Query: {query}, Engine: {search_engine}")
        
        try:
            response = await perform_search(query, search_engine)
            return response
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get_answer")
async def get_answer(request: QuestionRequest):
    try:
        answer = await get_search_sum(request.query, request.contexts)
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Error in get_answer: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating answer")

@app.post("/get_related_questions")
async def get_related_questions_endpoint(request: QuestionRequest):
    try:
        questions = await get_related_questions(request.query, request.contexts)
        return {"related_questions": questions}
    except Exception as e:
        logger.error(f"Error in get_related_questions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating related questions")

@app.post("/documents/{document_id}/summarize")
async def summarize_document(document_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Summarize a document using LLM"""
    logger.debug(f"Summarizing document {document_id} for user {current_user.username}")
    try:
        # Get the document
        document = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Check if user has access to the document
        if document.owner_id != current_user.id:
            share = db.query(DocumentShareModel).filter(
                DocumentShareModel.document_id == document_id,
                DocumentShareModel.shared_with_id == current_user.id
            ).first()
            if not share:
                logger.error(f"User {current_user.username} not authorized to access document {document_id}")
                raise HTTPException(status_code=403, detail="Not authorized to access this document")

        # Extract text content
        if not document.content:
            return {"summary": "This document is empty"}

        # Prepare prompt for the LLM
        prompt = f"""Please provide a concise summary of the following document. Focus on the main points and key ideas:

{document.content}

Summary:"""

        # Get summary from LLM
        try:
            logger.debug("Sending request to LLM API")
            response = completion(
                model="gpt-4o-mini",  # Using a more widely available model
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides clear and concise document summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.7
            )
            summary = response.choices[0].message.content.strip()
            logger.debug("Successfully generated summary")
            return {"summary": summary}
        except Exception as llm_error:
            logger.error(f"LLM API error: {str(llm_error)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error generating summary: {str(llm_error)}")

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error summarizing document: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error summarizing document: {str(e)}")

# Auth endpoints
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Received registration request for username: {user.username}")
    
    # Check email
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user:
        logger.warning(f"Email {user.email} already registered")
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Check username
    db_user = db.query(UserModel).filter(UserModel.username == user.username).first()
    if db_user:
        logger.warning(f"Username {user.username} already registered")
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    try:
        logger.info("Creating new user...")
        hashed_password = get_password_hash(user.password)
        db_user = UserModel(email=user.email, username=user.username, hashed_password=hashed_password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Successfully created user: {user.username}")
        return db_user
    except Exception as e:
        logger.error(f"Failed to create user: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user: {str(e)}"
        )

@app.post("/auth/verify")
async def verify_token(current_user: UserModel = Depends(get_current_user)):
    """Verify if the current token is valid."""
    return {"valid": True, "user": {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    }}

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(days=7)  # Token expires in 7 days
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username already exists
    if db.query(UserModel).filter(UserModel.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email already exists
    if db.query(UserModel).filter(UserModel.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = UserModel(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Document endpoints
@app.get("/documents", response_model=List[Document])
async def list_documents(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    logger.debug(f"Listing documents for user: {current_user.username}")
    try:
        # Get owned documents
        owned_documents = db.query(DocumentModel).filter(DocumentModel.owner_id == current_user.id).all()
        
        # Get shared documents
        shared_documents = db.query(DocumentModel).join(
            DocumentShareModel,
            DocumentModel.id == DocumentShareModel.document_id
        ).filter(
            DocumentShareModel.shared_with_id == current_user.id
        ).all()
        
        # Combine both lists
        all_documents = owned_documents + shared_documents
        logger.debug(f"Found {len(owned_documents)} owned and {len(shared_documents)} shared documents")
        return all_documents
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.get("/documents/shared", response_model=List[Document])
async def list_shared_documents(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """List documents shared with the current user"""
    logger.debug(f"Listing shared documents for user: {current_user.username}")
    try:
        documents = db.query(DocumentModel).join(
            DocumentShareModel,
            DocumentModel.id == DocumentShareModel.document_id
        ).filter(
            DocumentShareModel.shared_with_id == current_user.id
        ).all()
        logger.debug(f"Found {len(documents)} shared documents")
        return documents
    except Exception as e:
        logger.error(f"Error listing shared documents: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error listing shared documents: {str(e)}")

@app.post("/documents", response_model=Document)
async def create_document(document: DocumentCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    db_document = DocumentModel(**document.dict(), owner_id=current_user.id)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

@app.put("/documents/{document_id}", response_model=Document)
async def update_document(document_id: int, document: DocumentUpdate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update a document"""
    logger.debug(f"Attempting to update document {document_id} for user {current_user.username}")
    try:
        # Get the document with a lock for update
        db_document = db.query(DocumentModel).filter(
            DocumentModel.id == document_id
        ).with_for_update().first()
        
        if not db_document:
            logger.error(f"Document {document_id} not found")
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if user has access to edit the document
        if db_document.owner_id != current_user.id:
            # Check if document is shared with user
            share = db.query(DocumentShareModel).filter(
                DocumentShareModel.document_id == document_id,
                DocumentShareModel.shared_with_id == current_user.id
            ).first()
            
            if not share:
                logger.error(f"User {current_user.username} not authorized to edit document {document_id}")
                raise HTTPException(status_code=403, detail="Not authorized to edit this document")
        
        logger.debug(f"Found document {document_id}, proceeding with update")
        
        try:
            # Update only the fields that were provided
            update_data = document.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_document, key, value)
            
            db_document.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_document)
            
            logger.debug(f"Successfully updated document {document_id}")
            return db_document
            
        except Exception as db_error:
            logger.error(f"Database error while updating document: {str(db_error)}")
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred while updating document")
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating document {document_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")

@app.delete("/documents/{document_id}")
async def delete_document(document_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a document"""
    logger.debug(f"Attempting to delete document {document_id} for user {current_user.username}")
    try:
        # Get the document with a lock for update
        db_document = db.query(DocumentModel).filter(
            DocumentModel.id == document_id,
            DocumentModel.owner_id == current_user.id
        ).with_for_update().first()
        
        if not db_document:
            logger.error(f"Document {document_id} not found or not owned by user {current_user.username}")
            raise HTTPException(status_code=404, detail="Document not found")
        
        logger.debug(f"Found document {document_id}, proceeding with deletion")
        
        try:
            # Delete the document - shares will be automatically deleted due to cascade
            db.delete(db_document)
            db.commit()
            logger.debug(f"Successfully deleted document {document_id}")
            return {"message": "Document deleted successfully"}
            
        except Exception as db_error:
            logger.error(f"Database error while deleting document: {str(db_error)}")
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred while deleting document")
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@app.post("/documents/{document_id}/share")
async def share_document(document_id: int, share_data: DocumentShare, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Share a document with another user"""
    logger.debug(f"Attempting to share document {document_id} with user {share_data.username}")
    try:
        # Check if document exists and belongs to current user
        db_document = db.query(DocumentModel).filter(
            DocumentModel.id == document_id,
            DocumentModel.owner_id == current_user.id
        ).with_for_update().first()
        
        if not db_document:
            logger.error(f"Document {document_id} not found or not owned by user {current_user.username}")
            raise HTTPException(status_code=404, detail="Document not found or you don't have permission to share it")
        
        # Check if user to share with exists
        share_with_user = db.query(UserModel).filter(UserModel.username == share_data.username).first()
        if not share_with_user:
            logger.error(f"User {share_data.username} not found")
            raise HTTPException(status_code=404, detail=f"User {share_data.username} not found")
        
        # Don't allow sharing with yourself
        if share_with_user.id == current_user.id:
            logger.error(f"User {current_user.username} attempted to share document with themselves")
            raise HTTPException(status_code=400, detail="You cannot share a document with yourself")
        
        # Check if document is already shared with user
        existing_share = db.query(DocumentShareModel).filter(
            DocumentShareModel.document_id == document_id,
            DocumentShareModel.shared_with_id == share_with_user.id
        ).first()
        
        if existing_share:
            logger.error(f"Document {document_id} already shared with user {share_data.username}")
            raise HTTPException(status_code=400, detail=f"Document is already shared with {share_data.username}")
        
        try:
            # Create new share
            logger.debug(f"Creating share record for document {document_id} with user {share_data.username}")
            db_share = DocumentShareModel(
                document_id=document_id,
                shared_with_id=share_with_user.id
            )
            db.add(db_share)
            db.commit()
            logger.info(f"Successfully shared document {document_id} with user {share_data.username}")
            
            return {
                "message": f"Document shared successfully with {share_data.username}",
                "share_id": db_share.id
            }
            
        except Exception as db_error:
            logger.error(f"Database error while sharing document: {str(db_error)}")
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred while sharing document")
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error sharing document {document_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to share document: {str(e)}")

@app.post("/documents/{document_id}/move")
async def move_document(
    document_id: int,
    folder_id: Optional[int] = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get document
    document = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check ownership
    if document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to move this document")
    
    # If folder_id is provided, check if folder exists and belongs to user
    if folder_id:
        folder = db.query(FolderModel).filter(
            FolderModel.id == folder_id,
            FolderModel.owner_id == current_user.id
        ).first()
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
    
    # Move document
    document.folder_id = folder_id
    db.commit()
    return {"message": "Document moved successfully"}

def extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    # Handle different YouTube URL formats
    parsed_url = urlparse(url)
    if parsed_url.hostname in ('youtu.be', 'www.youtu.be'):
        return parsed_url.path[1:]
    if parsed_url.hostname in ('youtube.com', 'www.youtube.com'):
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query)['v'][0]
        if parsed_url.path.startswith('/embed/'):
            return parsed_url.path.split('/')[2]
        if parsed_url.path.startswith('/v/'):
            return parsed_url.path.split('/')[2]
    raise ValueError("Invalid YouTube URL")

def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

def get_transcript(video_id: str) -> list:
    """Get transcript from YouTube video."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript_list  # Return the full transcript list with timestamps
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not get transcript: {str(e)}")

@app.post("/youtube/summarize")
async def summarize_youtube_video(request: YouTubeRequest):
    try:
        # Extract video ID from URL
        video_id = extract_video_id(request.url)
        
        # Get video transcript with timestamps
        transcript_list = get_transcript(video_id)
        
        # Process transcript with timestamps
        processed_entries = []
        for entry in transcript_list:
            timestamp = format_timestamp(entry["start"])
            text = entry["text"].strip()  # Ensure text is stripped of whitespace
            processed_entries.append(f"{text} [{timestamp}]")  # Add timestamp as citation
        
        text = "\n\n".join(processed_entries)  # Use double newlines for better separation

        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=10000,  # Reduced chunk size to leave room for timestamps
            chunk_overlap=1000,  # Increased overlap to prevent cutting off context
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]  # Added period+space as separator
        )
        chunks = text_splitter.split_text(text)

        # Ensure timestamps aren't cut off at chunk boundaries
        for i in range(len(chunks)):
            # If chunk ends with an incomplete timestamp, find the last complete timestamp
            if '[' in chunks[i] and ']' not in chunks[i].split('[')[-1]:
                last_complete = chunks[i].rindex(']')
                if i + 1 < len(chunks):
                    # Move the incomplete part to the next chunk
                    chunks[i + 1] = chunks[i][last_complete + 1:] + chunks[i + 1]
                    chunks[i] = chunks[i][:last_complete + 1]
        
        # Generate summary for each chunk
        summaries = []
        failed_chunks = []
        for i, chunk in enumerate(chunks):
            try:
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that creates clear, well-structured summaries of YouTube video segments. For each key point or quote you mention, you MUST include the timestamp citation in [HH:MM:SS] format at the end of the sentence. If multiple points occur in sequence, combine their timestamps with a hyphen, like [HH:MM:SS-HH:MM:SS]. Keep the summary focused on key points and maintain chronological order. Keep the summary to 500 words or less."
                        },
                        {
                            "role": "user",
                            "content": f"Please summarize this segment of the transcript, making sure to cite timestamps for each key point. For sequential points, combine their timestamps with a hyphen [HH:MM:SS-HH:MM:SS]. Each point must have a timestamp citation at the end of its sentence. Never cut off timestamps:\n\n{chunk}"
                        }
                    ],
                    temperature=0.7
                )
                summaries.append(response.choices[0].message.content)
            except Exception as e:
                logger.error(f"Error summarizing chunk {i}: {str(e)}")
                failed_chunks.append(i)
                continue
        
        if not summaries:
            raise HTTPException(status_code=500, detail="Failed to generate summary")
        
        if failed_chunks:
            logger.warning(f"Failed to summarize chunks: {failed_chunks}")
        
        # Generate a final, cohesive summary
        combined_summary = "\n\n".join(summaries)
        final_response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that creates clear, well-structured final summaries of YouTube videos. Your task is to take multiple segment summaries and create a cohesive, chronological summary that PRESERVES ALL TIMESTAMP CITATIONS. For sequential points, combine their timestamps with a hyphen [HH:MM:SS-HH:MM:SS]. Keep the summary to 500 words or less. Format the summary in markdown with sections and bullet points. Never cut off or omit any timestamps. "
                },
                {
                    "role": "user",
                    "content": f"Create a final, cohesive summary from these segment summaries. Maintain chronological order and PRESERVE ALL TIMESTAMP CITATIONS. For sequential points or related ideas, combine their timestamps with a hyphen [HH:MM:SS-HH:MM:SS]. If you notice any gaps in the timeline, please note them:\n\n{combined_summary}"
                }
            ],
            temperature=0.7
        )
        
        return {"summary": final_response.choices[0].message.content}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error summarizing video: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to generate summary")

@app.get("/users/me", response_model=UserResponse)
async def get_current_user_details(current_user: UserModel = Depends(get_current_user)):
    """Get details of the currently authenticated user"""
    return current_user

# File endpoints
@app.get("/files", response_model=List[FileResponse])
async def list_files(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all files owned by or shared with the current user"""
    try:
        logger.debug(f"Listing files for user: {current_user.username}")
        
        # Get owned files
        owned_files = db.query(FileModel).filter(FileModel.owner_id == current_user.id).all()
        logger.debug(f"Found {len(owned_files)} owned files")
        
        # Get shared files
        shared_files = db.query(FileModel).join(
            FileShareModel,
            FileModel.id == FileShareModel.file_id
        ).filter(
            FileShareModel.shared_with_id == current_user.id
        ).all()
        logger.debug(f"Found {len(shared_files)} shared files")
        
        # Combine both lists and add download URLs
        all_files = owned_files + shared_files
        response_files = []
        
        for file in all_files:
            try:
                logger.debug(f"Processing file: {file.id} - {file.name}")
                file_dict = {
                    "id": file.id,
                    "name": file.name,
                    "size": file.size,
                    "created_at": file.created_at,
                    "owner_id": file.owner_id,
                    "url": f"{SERVER_HOST}/files/{file.id}/download"
                }
                logger.debug(f"Created file dict: {file_dict}")
                response_file = FileResponse(**file_dict)
                response_files.append(response_file)
            except Exception as file_error:
                logger.error(f"Error processing file {file.id}: {str(file_error)}")
                logger.error(f"File data: {vars(file)}")
                continue
        
        logger.debug(f"Returning {len(response_files)} total files")
        return response_files
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@app.post("/files/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a new file"""
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join("uploads", str(current_user.id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file to disk
        file_path = os.path.join(upload_dir, file.filename)
        file_size = 0
        
        with open(file_path, "wb") as f:
            while contents := await file.read(1024 * 1024):  # Read in 1MB chunks
                file_size += len(contents)
                f.write(contents)
                
                # Check file size limit (10MB)
                if file_size > 10 * 1024 * 1024:
                    os.remove(file_path)
                    raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        # Create file record in database
        db_file = FileModel(
            name=file.filename,
            path=file_path,
            size=file_size,
            owner_id=current_user.id
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        # Create response with download URL
        response_dict = {
            "id": db_file.id,
            "name": db_file.name,
            "size": db_file.size,
            "created_at": db_file.created_at,
            "owner_id": db_file.owner_id,
            "url": f"{SERVER_HOST}/files/{db_file.id}/download"
        }
        
        return FileResponse(**response_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/files/{file_id}/download")
async def download_file(
    file_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a file"""
    try:
        logger.debug(f"Download request for file {file_id} by user {current_user.username}")
        
        # Get file from database
        file = db.query(FileModel).filter(FileModel.id == file_id).first()
        if not file:
            logger.error(f"File {file_id} not found in database")
            raise HTTPException(status_code=404, detail="File not found")
        
        logger.debug(f"Found file in database: {file.name} at path {file.path}")
        
        # Check if user has access to file
        if file.owner_id != current_user.id:
            # Check if file is shared with user
            share = db.query(FileShareModel).filter(
                FileShareModel.file_id == file_id,
                FileShareModel.shared_with_id == current_user.id
            ).first()
            
            if not share:
                logger.error(f"User {current_user.username} not authorized to access file {file_id}")
                raise HTTPException(status_code=403, detail="Not authorized to access this file")
        
        # Check if file exists on disk
        if not os.path.exists(file.path):
            logger.error(f"File not found on disk at path: {file.path}")
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        # Log file details
        logger.debug(f"File details: size={os.path.getsize(file.path)}, exists={os.path.exists(file.path)}")
        
        try:
            # Import FileResponse from fastapi.responses
            from fastapi.responses import FileResponse as FastAPIFileResponse
            
            # Return file as response using FastAPIFileResponse
            return FastAPIFileResponse(
                path=file.path,
                filename=file.name,
                media_type='application/octet-stream'
            )
        except Exception as file_error:
            logger.error(f"Error creating FileResponse: {str(file_error)}")
            logger.error(f"File path: {file.path}")
            logger.error(f"File name: {file.name}")
            raise HTTPException(status_code=500, detail=f"Error serving file: {str(file_error)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/files/{file_id}")
async def delete_file(
    file_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a file"""
    try:
        # Get file from database
        file = db.query(FileModel).filter(
            FileModel.id == file_id,
            FileModel.owner_id == current_user.id
        ).first()
        
        if not file:
            raise HTTPException(status_code=404, detail="File not found or not authorized to delete")
        
        # Delete file from disk
        try:
            os.remove(file.path)
        except OSError:
            logger.warning(f"Could not delete file from disk: {file.path}")
        
        # Delete file record from database
        db.delete(file)
        db.commit()
        
        return {"message": "File deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/files/{file_id}/share")
async def share_file(
    file_id: int,
    share_data: DocumentShare,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Share a file with another user"""
    try:
        # Check if file exists and belongs to current user
        file = db.query(FileModel).filter(
            FileModel.id == file_id,
            FileModel.owner_id == current_user.id
        ).first()
        
        if not file:
            raise HTTPException(status_code=404, detail="File not found or not authorized to share")
        
        # Check if user to share with exists
        share_with_user = db.query(UserModel).filter(UserModel.username == share_data.username).first()
        if not share_with_user:
            raise HTTPException(status_code=404, detail=f"User {share_data.username} not found")
        
        # Don't allow sharing with yourself
        if share_with_user.id == current_user.id:
            raise HTTPException(status_code=400, detail="You cannot share a file with yourself")
        
        # Check if file is already shared with user
        existing_share = db.query(FileShareModel).filter(
            FileShareModel.file_id == file_id,
            FileShareModel.shared_with_id == share_with_user.id
        ).first()
        
        if existing_share:
            raise HTTPException(status_code=400, detail=f"File is already shared with {share_data.username}")
        
        # Create new share
        db_share = FileShareModel(
            file_id=file_id,
            shared_with_id=share_with_user.id
        )
        
        db.add(db_share)
        db.commit()
        
        return {
            "message": f"File shared successfully with {share_data.username}",
            "share_id": db_share.id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add new Pydantic models for photos
class PhotoMetadata(BaseModel):
    width: int
    height: int
    format: str
    taken_at: Optional[datetime]

class PhotoResponse(BaseModel):
    id: int
    name: str
    size: int
    created_at: datetime
    owner_id: int
    url: str
    metadata: Optional[PhotoMetadata]
    thumbnail_url: Optional[str]

    class Config:
        from_attributes = True

# Add photo-specific functions
def is_valid_image(file_path: str) -> bool:
    """Check if the file is a valid image"""
    try:
        # Special handling for AVIF/HEIF files
        if file_path.lower().endswith(('.avif', '.heic')):
            try:
                heif_file = pillow_heif.open_heif(file_path)
                return True
            except Exception as heif_error:
                logger.error(f"HEIF validation error for {file_path}: {str(heif_error)}")
                return False
        
        # Standard handling for other image formats
        with Image.open(file_path) as img:
            img.load()
            format = img.format.lower() if img.format else None
            supported_formats = {'jpeg', 'jpg', 'png', 'gif', 'webp'}
            return format in supported_formats
    except Exception as e:
        logger.error(f"Image validation error for {file_path}: {str(e)}")
        return False

def create_thumbnail(file_path: str, max_size: int = 300) -> Optional[str]:
    """Create a thumbnail for the image"""
    try:
        # Get the directory of the original file
        file_dir = os.path.dirname(file_path)
        thumbnail_name = f"thumb_{os.path.basename(file_path)}"
        thumbnail_path = os.path.join(file_dir, thumbnail_name)
        
        # Special handling for AVIF/HEIF files
        if file_path.lower().endswith(('.avif', '.heic')):
            try:
                heif_file = pillow_heif.open_heif(file_path)
                # Get the primary image
                image = heif_file.to_pillow()
            except Exception as heif_error:
                logger.error(f"HEIF thumbnail error for {file_path}: {str(heif_error)}")
                return None
        else:
            image = Image.open(file_path)
        
        # Convert to RGB if necessary
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        
        # Calculate thumbnail size while maintaining aspect ratio
        width, height = image.size
        ratio = min(max_size / width, max_size / height)
        new_size = (int(width * ratio), int(height * ratio))
        
        # Create thumbnail using resize with LANCZOS filter for better quality
        thumbnail = image.resize(new_size, Image.Resampling.LANCZOS)
        thumbnail.save(thumbnail_path, "JPEG", quality=85, optimize=True)
        
        return thumbnail_path
    except Exception as e:
        logger.error(f"Error creating thumbnail for {file_path}: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def get_image_metadata(file_path: str) -> Optional[PhotoMetadata]:
    """Get metadata from an image file"""
    try:
        # Special handling for AVIF/HEIF files
        if file_path.lower().endswith(('.avif', '.heic')):
            try:
                heif_file = pillow_heif.open_heif(file_path)
                format = 'avif' if file_path.lower().endswith('.avif') else 'heic'
                metadata = {
                    "width": heif_file.size[0],
                    "height": heif_file.size[1],
                    "format": format,
                    "taken_at": None
                }
                return PhotoMetadata(**metadata)
            except Exception as heif_error:
                logger.error(f"HEIF metadata error for {file_path}: {str(heif_error)}")
                return None
        
        # Standard handling for other image formats
        with Image.open(file_path) as img:
            metadata = {
                "width": img.width,
                "height": img.height,
                "format": img.format.lower() if img.format else 'unknown',
                "taken_at": None
            }
            return PhotoMetadata(**metadata)
    except Exception as e:
        logger.error(f"Error getting image metadata: {str(e)}")
        logger.error(traceback.format_exc())
        return None

# Enhance existing file endpoints for photos

@app.get("/photos", response_model=List[PhotoResponse])
async def list_photos(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all photos (image files) owned by or shared with the current user"""
    try:
        logger.debug(f"Listing photos for user: {current_user.username}")
        
        # Define image extensions (both lower and upper case)
        image_extensions = [
            '%.jpg', '%.jpeg', '%.png', '%.gif', '%.webp', '%.avif',
            '%.JPG', '%.JPEG', '%.PNG', '%.GIF', '%.WEBP', '%.AVIF'
        ]
        
        # Get owned files that are images using LIKE for SQLite compatibility
        owned_files = db.query(FileModel).filter(
            FileModel.owner_id == current_user.id,
            or_(*[FileModel.name.like(ext) for ext in image_extensions])
        ).all()
        
        # Get shared files that are images
        shared_files = db.query(FileModel).join(
            FileShareModel,
            FileModel.id == FileShareModel.file_id
        ).filter(
            FileShareModel.shared_with_id == current_user.id,
            or_(*[FileModel.name.like(ext) for ext in image_extensions])
        ).all()
        
        # Combine both lists and add photo-specific information
        all_photos = owned_files + shared_files
        response_photos = []
        
        for photo in all_photos:
            try:
                metadata = get_image_metadata(photo.path)
                thumbnail_path = create_thumbnail(photo.path)
                
                photo_dict = {
                    "id": photo.id,
                    "name": photo.name,
                    "size": photo.size,
                    "created_at": photo.created_at,
                    "owner_id": photo.owner_id,
                    "url": f"{SERVER_HOST}/files/{photo.id}/content",
                    "metadata": metadata,
                    "thumbnail_url": f"{SERVER_HOST}/files/{photo.id}/thumbnail" if thumbnail_path else None
                }
                
                response_photos.append(PhotoResponse(**photo_dict))
            except Exception as photo_error:
                logger.error(f"Error processing photo {photo.id}: {str(photo_error)}")
                continue
        
        return response_photos
    except Exception as e:
        logger.error(f"Error listing photos: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error listing photos: {str(e)}")

@app.post("/photos/upload", response_model=PhotoResponse)
async def upload_photo(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a new photo with validation and thumbnail generation"""
    try:
        # Validate file type
        content_type = file.content_type
        if not content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image (image/*)")
        
        # Validate file extension
        filename = file.filename.lower()
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif'}
        if not any(filename.endswith(ext) for ext in valid_extensions):
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Supported types: {', '.join(valid_extensions)}")
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join("uploads", str(current_user.id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file to disk
        file_path = os.path.join(upload_dir, file.filename)
        file_size = 0
        
        try:
            with open(file_path, "wb") as f:
                while contents := await file.read(1024 * 1024):  # Read in 1MB chunks
                    file_size += len(contents)
                    if file_size > 10 * 1024 * 1024:  # Check size before writing
                        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
                    f.write(contents)
        except Exception as write_error:
            # Clean up the partially written file
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=400, detail=f"Error saving file: {str(write_error)}")
        
        # Validate that it's a valid image file
        if not is_valid_image(file_path):
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Invalid or corrupted image file")
        
        # Create thumbnail
        thumbnail_path = create_thumbnail(file_path)
        if not thumbnail_path:
            logger.error(f"Failed to create thumbnail for {file_path}")
            # Don't fail the upload if thumbnail creation fails
        
        # Get image metadata
        metadata = get_image_metadata(file_path)
        if not metadata:
            logger.error(f"Failed to get metadata for {file_path}")
            # Don't fail the upload if metadata extraction fails
        
        # Create file record in database
        db_file = FileModel(
            name=file.filename,
            path=file_path,
            size=file_size,
            owner_id=current_user.id
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        # Create response
        response_dict = {
            "id": db_file.id,
            "name": db_file.name,
            "size": db_file.size,
            "created_at": db_file.created_at,
            "owner_id": db_file.owner_id,
            "url": f"{SERVER_HOST}/files/{db_file.id}/content",
            "metadata": metadata,
            "thumbnail_url": f"{SERVER_HOST}/files/{db_file.id}/thumbnail" if thumbnail_path else None
        }
        
        return PhotoResponse(**response_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading photo: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error uploading photo: {str(e)}")

@app.get("/files/{file_id}/thumbnail")
async def get_file_thumbnail(
    file_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a thumbnail for an image file with authentication"""
    try:
        # Get the file record
        file = db.query(FileModel).filter(FileModel.id == file_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
            
        # Check if user has access to the file
        if file.owner_id != current_user.id:
            # Check if file is shared with the user
            shared = db.query(FileShareModel).filter(
                FileShareModel.file_id == file_id,
                FileShareModel.shared_with_id == current_user.id
            ).first()
            if not shared:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Get the thumbnail path
        file_dir = os.path.dirname(file.path)
        thumbnail_name = f"thumb_{os.path.basename(file.path)}"
        thumbnail_path = os.path.join(file_dir, thumbnail_name)
        
        # Create thumbnail if it doesn't exist
        if not os.path.exists(thumbnail_path):
            thumbnail_path = create_thumbnail(file.path)
            if not thumbnail_path:
                logger.error(f"Failed to create thumbnail for file {file_id}")
                raise HTTPException(status_code=500, detail="Could not create thumbnail")
        
        # Verify the thumbnail exists
        if not os.path.exists(thumbnail_path):
            logger.error(f"Thumbnail file not found at {thumbnail_path}")
            raise HTTPException(status_code=404, detail="Thumbnail not found")
            
        # Use FastAPI's FileResponse directly
        return fastapi.responses.FileResponse(
            path=thumbnail_path,
            media_type='image/jpeg',
            filename=f"thumb_{file.name}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting thumbnail for file {file_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error getting thumbnail: {str(e)}")

@app.get("/files/{file_id}/content")
async def get_photo_content(
    file_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the full-size photo content"""
    try:
        # Get file from database
        file = db.query(FileModel).filter(FileModel.id == file_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if user has access to file
        if file.owner_id != current_user.id:
            share = db.query(FileShareModel).filter(
                FileShareModel.file_id == file_id,
                FileShareModel.shared_with_id == current_user.id
            ).first()
            
            if not share:
                raise HTTPException(status_code=403, detail="Not authorized to access this file")
        
        # Check if file exists
        if not os.path.exists(file.path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        # Determine content type based on file extension
        content_type = 'image/jpeg'  # default
        if file.name.lower().endswith('.png'):
            content_type = 'image/png'
        elif file.name.lower().endswith('.gif'):
            content_type = 'image/gif'
        elif file.name.lower().endswith('.webp'):
            content_type = 'image/webp'
        elif file.name.lower().endswith('.avif'):
            content_type = 'image/avif'
        
        # Use FastAPI's FileResponse directly
        return fastapi.responses.FileResponse(
            path=file.path,
            media_type=content_type,
            filename=file.name
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting photo content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/files/{file_id}/subtitle")
async def generate_photo_subtitle(
    file_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate an AI subtitle for a photo using GPT-4o-mini"""
    try:
        # Get the file record
        file = db.query(FileModel).filter(FileModel.id == file_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
            
        # Check if user has access to the file
        if file.owner_id != current_user.id:
            # Check if file is shared with the user
            shared = db.query(FileShareModel).filter(
                FileShareModel.file_id == file_id,
                FileShareModel.shared_with_id == current_user.id
            ).first()
            if not shared:
                raise HTTPException(status_code=403, detail="Access denied")

        # Get image metadata
        metadata = get_image_metadata(file.path)
        if not metadata:
            raise HTTPException(status_code=400, detail="Could not extract image metadata")

        # Prepare prompt for GPT-4o-mini
        prompt = f"""You are an AI assistant that generates creative and engaging subtitles for photos.
Given an image with the following properties:
- Name: {file.name}
- Format: {metadata.format}
- Dimensions: {metadata.width}×{metadata.height}

Please generate a creative and engaging subtitle that could be used as a caption for this photo.
Keep the subtitle concise (1-2 sentences) and make it engaging."""

        # Generate subtitle using GPT-4o-mini
        response = completion(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a creative AI assistant that generates engaging photo subtitles."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.7
        )

        subtitle = response.choices[0].message.content.strip()
        return {"subtitle": subtitle}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating subtitle: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating subtitle: {str(e)}")

@app.post("/rooms", response_model=Room)
async def create_room(
    room_data: RoomCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new video call room"""
    try:
        # Validate room name
        if len(room_data.room_name.strip()) < 3:
            raise HTTPException(status_code=400, detail="Room name must be at least 3 characters long")
            
        room_id = f"room_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{current_user.id}"
        db_room = RoomModel(
            id=room_id,
            name=room_data.room_name.strip(),
            created_by=current_user.id
        )
        db.add(db_room)
        db.commit()
        db.refresh(db_room)
        
        return Room(
            id=db_room.id,
            name=db_room.name,
            created_by=current_user.username,
            created_at=db_room.created_at,
            participants=[]
        )
    except Exception as e:
        logger.error(f"Error creating room: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rooms", response_model=List[Room])
async def list_rooms(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all active video call rooms"""
    try:
        rooms = db.query(RoomModel).all()
        return [
            Room(
                id=room.id,
                name=room.name,
                created_by=db.query(UserModel).filter(UserModel.id == room.created_by).first().username,
                created_at=room.created_at,
                participants=list(manager.room_participants.get(room.id, set()))
            )
            for room in rooms
        ]
    except Exception as e:
        logger.error(f"Error listing rooms: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/rooms/{room_id}")
async def delete_room(
    room_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a video call room"""
    try:
        room = db.query(RoomModel).filter(
            RoomModel.id == room_id,
            RoomModel.created_by == current_user.id
        ).first()
        
        if not room:
            raise HTTPException(status_code=404, detail="Room not found or not authorized to delete")
        
        # Close all WebSocket connections for this room
        if room_id in manager.active_connections:
            connections = manager.active_connections[room_id].copy()
            for user_id, connection in connections.items():
                try:
                    await connection.close()
                except:
                    pass
                manager.disconnect(room_id, user_id)
        
        # Delete room from database
        db.delete(room)
        db.commit()
        
        return {"message": "Room deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting room: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def fetch_news_from_api() -> List[NewsArticle]:
    """Fetch news from NewsAPI."""
    try:
        api_key = os.environ.get("NEWS_API_KEY")
        if not api_key:
            raise ValueError("NEWS_API_KEY environment variable not set")

        async with aiohttp.ClientSession() as session:
            # Fetch top headlines from multiple categories
            categories = ["technology", "science", "business"]
            all_articles = []
            
            for category in categories:
                url = f"https://newsapi.org/v2/top-headlines"
                params = {
                    "apiKey": api_key,
                    "category": category,
                    "language": "en",
                    "pageSize": 5  # Get 5 articles per category
                }
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"NewsAPI error: {await response.text()}")
                        continue
                        
                    data = await response.json()
                    if data.get("status") != "ok":
                        logger.error(f"NewsAPI returned error: {data}")
                        continue
                        
                    articles = data.get("articles", [])
                    for article in articles:
                        # Generate a unique ID for each article
                        article_id = str(hash(article["url"]))
                        
                        # Create a summary using GPT-4o-mini
                        try:
                            summary_response = completion(
                                model="gpt-4o-mini",
                                messages=[
                                    {"role": "system", "content": "You are a helpful assistant that creates concise news summaries."},
                                    {"role": "user", "content": f"Please provide a concise 2-3 sentence summary of this news article:\n\nTitle: {article['title']}\n\nDescription: {article['description']}"}
                                ],
                                max_tokens=100,
                                temperature=0.7
                            )
                            summary = summary_response.choices[0].message.content.strip()
                        except Exception as e:
                            logger.error(f"Error generating summary: {str(e)}")
                            summary = article.get("description", "Summary not available")

                        news_article = NewsArticle(
                            id=article_id,
                            title=article["title"],
                            url=article["url"],
                            image_url=article.get("urlToImage"),
                            summary=summary
                        )
                        all_articles.append(news_article)

            # Shuffle articles to mix categories
            random.shuffle(all_articles)
            return all_articles[:10]  # Return top 10 articles

    except Exception as e:
        logger.error(f"Error fetching news: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch news: {str(e)}"
        )

@app.get("/news/recommendations", response_model=List[NewsArticle])
@cache(expire=300)  # Cache for 5 minutes
async def get_news_recommendations(
    page: int = 1,
    page_size: int = 12,
    current_user: User = Depends(get_current_user)
):
    try:
        # Calculate offset
        offset = (page - 1) * page_size

        # Fetch all news (this will use cache if available)
        all_news = await fetch_news_from_api()
        
        # Apply pagination
        paginated_news = all_news[offset:offset + page_size]
        
        return paginated_news
    except Exception as e:
        logger.error(f"Error fetching news recommendations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch news recommendations"
        )

def get_amazon_paapi_client():
    """Initialize Amazon Product Advertising API client"""
    try:
        config = Config(
            region_name='us-west-2',
            signature_version='v4',
            retries={
                'max_attempts': 3,
                'mode': 'standard'
            }
        )
        return boto3.client(
            'paapi5',
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            config=config
        )
    except Exception as e:
        logger.error(f"Error initializing Amazon PAAPI client: {str(e)}")
        return None

async def fetch_deals_from_api() -> List[Deal]:
    """Fetch real deals from Google Shopping via SerpApi"""
    try:
        api_key = os.environ["SERPAPI_API_KEY"]
        
        # Categories for shopping searches
        categories = [
            "electronics deals",
            "home appliance deals",
            "laptop deals",
            "smartphone deals",
            "gaming deals",
            "headphones deals",
            "smart home deals"
        ]
        
        # Randomly select two categories
        selected_categories = random.sample(categories, 2)
        all_deals = []
        
        async with aiohttp.ClientSession() as session:
            for category in selected_categories:
                try:
                    # SerpApi Google Shopping endpoint
                    url = "https://serpapi.com/search.json"
                    params = {
                        "api_key": api_key,
                        "engine": "google_shopping",
                        "q": category,
                        "google_domain": "google.com",
                        "gl": "us",  # Set location to US
                        "hl": "en",  # Set language to English
                        "sort_by": "price_low_to_high",
                        "price_low": 50,  # Min price $50
                        "discount": "include",  # Only show items with discounts
                        "num": 5  # Number of results per category
                    }
                    
                    logger.debug(f"Fetching deals for category: {category}")
                    async with session.get(url, params=params) as response:
                        response_text = await response.text()
                        logger.debug(f"API Response: {response_text[:200]}...")  # Log first 200 chars
                        
                        if response.status == 200:
                            try:
                                data = json.loads(response_text)
                                shopping_results = data.get('shopping_results', [])
                                
                                if not shopping_results:
                                    logger.warning(f"No shopping results found for category: {category}")
                                    continue
                                
                                for item in shopping_results:
                                    # Extract and format price information
                                    price = item.get('price', '')
                                    original_price = item.get('original_price', '')
                                    
                                    # Calculate discount if both prices are available
                                    discount_text = ""
                                    if price and original_price:
                                        try:
                                            current_price = float(price.replace('$', '').replace(',', ''))
                                            orig_price = float(original_price.replace('$', '').replace(',', ''))
                                            if orig_price > current_price:
                                                discount = round(((orig_price - current_price) / orig_price) * 100)
                                                discount_text = f" (Save {discount}%)"
                                        except (ValueError, TypeError) as e:
                                            logger.error(f"Error calculating discount: {str(e)}")
                                            pass
                                    
                                    price_display = f"{price}{discount_text}"
                                    
                                    # Get the correct product URL
                                    product_url = item.get('link', '')  # Direct product link
                                    if not product_url:
                                        product_url = item.get('product_link', '')  # Backup link
                                    if not product_url:
                                        # If no direct link, try to construct from product ID
                                        product_id = item.get('product_id', '')
                                        if product_id:
                                            product_url = f"https://www.google.com/shopping/product/{product_id}"
                                    
                                    # Create deal object
                                    deal = {
                                        "id": hash(item.get('product_id', '') or item.get('link', '')),
                                        "title": item.get('title', 'Unknown Product'),
                                        "image_url": item.get('thumbnail', ''),
                                        "summary": item.get('snippet', 'No description available'),
                                        "price": price_display,
                                        "url": product_url,
                                        "created_at": datetime.utcnow()
                                    }
                                    
                                    # Only add deals with valid URLs
                                    if product_url:
                                        all_deals.append(deal)
                                        logger.debug(f"Added deal with URL: {product_url}")
                                    else:
                                        logger.warning(f"Skipped deal without URL: {item.get('title', 'Unknown')}")
                                        
                            except json.JSONDecodeError as json_error:
                                logger.error(f"Error parsing JSON response: {str(json_error)}")
                                continue
                        else:
                            logger.error(f"API request failed with status {response.status}: {response_text}")
                                
                except Exception as category_error:
                    logger.error(f"Error fetching deals for category {category}: {str(category_error)}")
                    continue

        # If API call fails, fall back to backup deals data
        if not all_deals:
            logger.warning("No deals found from Google Shopping API, using backup data")
            return await fetch_backup_deals()

        # Randomize the order of deals
        random.shuffle(all_deals)
        return [Deal(**deal) for deal in all_deals[:6]]  # Return up to 6 deals

    except Exception as e:
        logger.error(f"Error fetching deals from Google Shopping API: {str(e)}")
        return await fetch_backup_deals()

async def fetch_backup_deals() -> List[Deal]:
    """Backup deals data in case API fails"""
    current_time = datetime.utcnow()
    mock_deals = [
        {
            "id": 1,
            "title": "Sony WH-1000XM4 Wireless Noise-Canceling Headphones",
            "image_url": "https://m.media-amazon.com/images/I/71o8Q5XJS5L._AC_SL1500_.jpg",
            "summary": "Industry-leading noise canceling with Dual Noise Sensor technology, 30-hour battery life, Touch Sensor controls, Speak-to-chat technology",
            "price": "$248.00 (Save 29%)",
            "url": "https://www.google.com/shopping/product/sony-wh1000xm4",
            "created_at": current_time
        },
        {
            "id": 2,
            "title": "Samsung Galaxy S23 Ultra 256GB",
            "image_url": "https://m.media-amazon.com/images/I/71HtN4qqLZL._AC_SL1500_.jpg",
            "summary": "6.8\" Dynamic AMOLED Display, 200MP Camera, S Pen functionality, 5G capability, 256GB Storage",
            "price": "$999.99 (Save $200)",
            "url": "https://www.google.com/shopping/product/samsung-galaxy-s23-ultra",
            "created_at": current_time
        },
        {
            "id": 3,
            "title": "LG C2 65\" OLED 4K Smart TV",
            "image_url": "https://m.media-amazon.com/images/I/81LHYqe9H1L._AC_SL1500_.jpg",
            "summary": "OLED evo Gallery Edition, AI-Powered 4K, Dolby Vision IQ & Dolby Atmos, Gaming Features, Gallery Design",
            "price": "$1,596.99 (Save $903)",
            "url": "https://www.google.com/shopping/product/lg-c2-oled",
            "created_at": current_time
        }
    ]
    return [Deal(**deal) for deal in mock_deals]

@app.get("/deals/recommendations", response_model=List[Deal])
async def get_deals_recommendations(current_user: User = Depends(get_current_user)):
    """Get recommended deals for the user"""
    try:
        deals = await fetch_deals_from_api()
        return deals
    except Exception as e:
        logger.error(f"Error getting deal recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch deal recommendations"
        )

@app.post("/deals/summarize")
async def summarize_deal_description(
    data: dict,
    current_user: User = Depends(get_current_user)
):
    """Generate an AI summary for a deal description"""
    try:
        description = data.get("description")
        if not description:
            raise HTTPException(status_code=400, detail="Description is required")

        # Prepare prompt for the LLM
        prompt = f"""Please provide a concise and engaging summary of this product description in 1-2 sentences. Focus on the key features and benefits:

{description}

Summary:"""

        # Generate summary using LLM
        response = completion(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates concise and engaging product summaries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.7
        )

        summary = response.choices[0].message.content.strip()
        return {"summary": summary}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error generating deal summary: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating summary: {str(e)}"
        )

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost", encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

@app.post("/voice-memos/transcribe")
async def transcribe_voice_memo(
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        # Validate content type
        if not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")

        logger.info(f"Received audio file: {audio.filename}, type: {audio.content_type}, size: {audio.size}")

        # Save the uploaded audio file temporarily
        suffix = '.webm'  # default
        if audio.content_type == 'audio/mp4':
            suffix = '.m4a'
        elif audio.content_type == 'audio/ogg':
            suffix = '.ogg'

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
            try:
                content = await audio.read()
                if not content:
                    raise HTTPException(status_code=400, detail="Empty audio file received")
                
                logger.info(f"Audio file size: {len(content)} bytes")
                temp_audio.write(content)
                temp_audio.flush()
                
                # Transcribe using OpenAI Whisper
                try:
                    # Create a new OpenAI client instance
                    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
                    
                    with open(temp_audio.name, 'rb') as audio_file:
                        logger.info("Starting transcription with Whisper API")
                        transcript_response = await client.audio.transcriptions.create(
                            file=audio_file,
                            model="whisper-1",
                            response_format="text"
                        )
                        transcript = transcript_response
                    
                    if not transcript:
                        raise HTTPException(status_code=500, detail="No transcription generated")
                    
                    logger.info(f"Transcription successful, length: {len(transcript)}")
                    
                    # Generate summary using GPT
                    try:
                        summary_prompt = f"Please provide a concise summary of the following transcription:\n\n{transcript}"
                        summary_response = await client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "You are a helpful assistant that provides concise summaries."},
                                {"role": "user", "content": summary_prompt}
                            ],
                            max_tokens=150,
                            temperature=0.7
                        )
                        
                        summary = summary_response.choices[0].message.content
                        logger.info("Summary generation successful")
                        
                        return {
                            "transcription": transcript,
                            "summary": summary
                        }
                    except Exception as summary_error:
                        logger.error(f"Summary generation failed: {str(summary_error)}")
                        # Return transcription even if summary fails
                        return {
                            "transcription": transcript,
                            "summary": "Summary generation failed"
                        }
                        
                except Exception as whisper_error:
                    logger.error(f"Whisper transcription failed: {str(whisper_error)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Transcription failed: {str(whisper_error)}"
                    )
                    
            except Exception as process_error:
                logger.error(f"Error processing audio: {str(process_error)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error processing audio: {str(process_error)}"
                )
            finally:
                # Clean up temporary file
                try:
                    if os.path.exists(temp_audio.name):
                        os.unlink(temp_audio.name)
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up temporary file: {str(cleanup_error)}")
                    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error handling voice memo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice-memos", response_model=VoiceMemo)
async def create_voice_memo(
    audio: UploadFile = File(...),
    duration: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join("uploads", str(current_user.id), "voice_memos")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"voice_memo_{timestamp}.webm"
        file_path = os.path.join(upload_dir, filename)
        
        # Save file to disk
        with open(file_path, "wb") as f:
            content = await audio.read()
            f.write(content)
        
        # Create voice memo record in database
        db_memo = VoiceMemoModel(
            filename=filename,
            path=file_path,
            duration=duration,
            owner_id=current_user.id
        )
        
        db.add(db_memo)
        db.commit()
        db.refresh(db_memo)
        
        return db_memo
        
    except Exception as e:
        logger.error(f"Error creating voice memo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voice-memos", response_model=List[VoiceMemo])
async def list_voice_memos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        memos = db.query(VoiceMemoModel).filter(
            VoiceMemoModel.owner_id == current_user.id
        ).order_by(VoiceMemoModel.created_at.desc()).all()
        return memos
    except Exception as e:
        logger.error(f"Error listing voice memos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voice-memos/{memo_id}/audio")
async def get_voice_memo_audio(
    memo_id: int,
    token: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Get the voice memo
        memo = db.query(VoiceMemoModel).filter(
            VoiceMemoModel.id == memo_id,
            VoiceMemoModel.owner_id == current_user.id
        ).first()
        
        if not memo:
            raise HTTPException(status_code=404, detail="Voice memo not found")
            
        if not os.path.exists(memo.path):
            raise HTTPException(status_code=404, detail="Audio file not found")
            
        # Use fastapi.responses.FileResponse directly
        return fastapi.responses.FileResponse(
            path=memo.path,
            media_type='audio/webm',
            filename=memo.filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting voice memo audio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/voice-memos/{memo_id}")
async def delete_voice_memo(
    memo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        memo = db.query(VoiceMemoModel).filter(
            VoiceMemoModel.id == memo_id,
            VoiceMemoModel.owner_id == current_user.id
        ).first()
        
        if not memo:
            raise HTTPException(status_code=404, detail="Voice memo not found")
            
        # Delete file from disk
        try:
            if os.path.exists(memo.path):
                os.remove(memo.path)
        except OSError as e:
            logger.error(f"Error deleting voice memo file: {str(e)}")
            
        # Delete record from database
        db.delete(memo)
        db.commit()
        
        return {"message": "Voice memo deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting voice memo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Update the transcribe endpoint to save transcription and summary
@app.post("/voice-memos/{memo_id}/transcribe")
async def transcribe_voice_memo(
    memo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Get the voice memo
        memo = db.query(VoiceMemoModel).filter(
            VoiceMemoModel.id == memo_id,
            VoiceMemoModel.owner_id == current_user.id
        ).first()
        
        if not memo:
            raise HTTPException(status_code=404, detail="Voice memo not found")
            
        if not os.path.exists(memo.path):
            raise HTTPException(status_code=404, detail="Audio file not found")
            
        # Transcribe using OpenAI Whisper
        try:
            client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
            
            with open(memo.path, 'rb') as audio_file:
                logger.info("Starting transcription with Whisper API")
                transcript_response = await client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-1",
                    response_format="text"
                )
                transcript = transcript_response
            
            if not transcript:
                raise HTTPException(status_code=500, detail="No transcription generated")
            
            # Generate summary using GPT
            try:
                summary_prompt = f"Please provide a concise summary of the following transcription:\n\n{transcript}"
                summary_response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that provides concise summaries."},
                        {"role": "user", "content": summary_prompt}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                
                summary = summary_response.choices[0].message.content
                
                # Update the database record
                memo.transcription = transcript
                memo.summary = summary
                db.commit()
                
                return {
                    "transcription": transcript,
                    "summary": summary
                }
                
            except Exception as summary_error:
                logger.error(f"Summary generation failed: {str(summary_error)}")
                # Save transcription even if summary fails
                memo.transcription = transcript
                db.commit()
                
                return {
                    "transcription": transcript,
                    "summary": "Summary generation failed"
                }
                
        except Exception as whisper_error:
            logger.error(f"Whisper transcription failed: {str(whisper_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Transcription failed: {str(whisper_error)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transcribing voice memo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/health/weight", response_model=WeightRecord)
async def save_weight(weight_data: WeightRecordCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    weight_record = WeightRecordModel(
        weight=weight_data.weight,
        date=weight_data.date or datetime.utcnow(),
        owner_id=current_user.id
    )
    db.add(weight_record)
    db.commit()
    db.refresh(weight_record)
    return weight_record

@app.get("/health/weight", response_model=List[WeightRecord])
async def get_weight_history(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    weight_records = db.query(WeightRecordModel).filter(
        WeightRecordModel.owner_id == current_user.id
    ).order_by(WeightRecordModel.date.desc()).all()
    return weight_records

@app.post("/health/height", response_model=HeightRecord)
async def save_height(height_data: HeightRecordCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    height_record = HeightRecordModel(
        height=height_data.height,
        date=height_data.date or datetime.utcnow(),
        owner_id=current_user.id
    )
    db.add(height_record)
    db.commit()
    db.refresh(height_record)
    return height_record

@app.get("/health/height", response_model=List[HeightRecord])
async def get_height_history(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    height_records = db.query(HeightRecordModel).filter(
        HeightRecordModel.owner_id == current_user.id
    ).order_by(HeightRecordModel.date.desc()).all()
    return height_records

@app.post("/health/heart-rate", response_model=HeartRateRecord)
async def save_heart_rate(heart_rate_data: HeartRateRecordCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    heart_rate_record = HeartRateRecordModel(
        heart_rate=heart_rate_data.heart_rate,
        activity_state=heart_rate_data.activity_state,
        date=heart_rate_data.date or datetime.utcnow(),
        owner_id=current_user.id
    )
    db.add(heart_rate_record)
    db.commit()
    db.refresh(heart_rate_record)
    return heart_rate_record

@app.get("/health/heart-rate", response_model=List[HeartRateRecord])
async def get_heart_rate_history(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    heart_rate_records = db.query(HeartRateRecordModel).filter(
        HeartRateRecordModel.owner_id == current_user.id
    ).order_by(HeartRateRecordModel.date.desc()).all()
    return heart_rate_records

@app.post("/health/blood-pressure", response_model=BloodPressureRecord)
async def save_blood_pressure(blood_pressure_data: BloodPressureRecordCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    blood_pressure_record = BloodPressureRecordModel(
        systolic=blood_pressure_data.systolic,
        diastolic=blood_pressure_data.diastolic,
        date=blood_pressure_data.date or datetime.utcnow(),
        notes=blood_pressure_data.notes,
        owner_id=current_user.id
    )
    db.add(blood_pressure_record)
    db.commit()
    db.refresh(blood_pressure_record)
    return blood_pressure_record

@app.get("/health/blood-pressure", response_model=List[BloodPressureRecord])
async def get_blood_pressure_history(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    blood_pressure_records = db.query(BloodPressureRecordModel).filter(
        BloodPressureRecordModel.owner_id == current_user.id
    ).order_by(BloodPressureRecordModel.date.desc()).all()
    return blood_pressure_records

@app.post("/health/visits", response_model=DoctorVisit)
async def save_doctor_visit(visit: DoctorVisitCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    visit_record = DoctorVisitModel(
        date=visit.date or datetime.utcnow(),
        doctor_name=visit.doctor_name,
        reason=visit.reason,
        notes=visit.notes,
        owner_id=current_user.id
    )
    db.add(visit_record)
    db.commit()
    db.refresh(visit_record)
    return visit_record

@app.get("/health/visits", response_model=List[DoctorVisit])
async def get_doctor_visits(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    visits = db.query(DoctorVisitModel).filter(
        DoctorVisitModel.owner_id == current_user.id
    ).order_by(DoctorVisitModel.date.desc()).all()
    return visits

@app.post("/health/goals/exercise", response_model=ExerciseGoals)
async def save_exercise_goals(goals: ExerciseGoalsCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    existing_goals = db.query(ExerciseGoalsModel).filter(
        ExerciseGoalsModel.owner_id == current_user.id
    ).first()
    
    if existing_goals:
        existing_goals.daily_steps = goals.daily_steps
        existing_goals.weekly_exercise_minutes = goals.weekly_exercise_minutes
    else:
        existing_goals = ExerciseGoalsModel(
            daily_steps=goals.daily_steps,
            weekly_exercise_minutes=goals.weekly_exercise_minutes,
            owner_id=current_user.id
        )
        db.add(existing_goals)
    
    db.commit()
    db.refresh(existing_goals)
    return existing_goals

@app.get("/health/goals/exercise", response_model=ExerciseGoals)
async def get_exercise_goals(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    goals = db.query(ExerciseGoalsModel).filter(
        ExerciseGoalsModel.owner_id == current_user.id
    ).first()
    if not goals:
        goals = ExerciseGoalsModel(
            daily_steps=0,
            weekly_exercise_minutes=0,
            owner_id=current_user.id
        )
        db.add(goals)
        db.commit()
        db.refresh(goals)
    return goals

@app.post("/health/goals/dietary", response_model=DietaryGoals)
async def save_dietary_goals(goals: DietaryGoalsCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    existing_goals = db.query(DietaryGoalsModel).filter(
        DietaryGoalsModel.owner_id == current_user.id
    ).first()
    
    if existing_goals:
        existing_goals.daily_calories = goals.daily_calories
        existing_goals.water_intake = goals.water_intake
    else:
        existing_goals = DietaryGoalsModel(
            daily_calories=goals.daily_calories,
            water_intake=goals.water_intake,
            owner_id=current_user.id
        )
        db.add(existing_goals)
    
    db.commit()
    db.refresh(existing_goals)
    return existing_goals

@app.get("/health/goals/dietary", response_model=DietaryGoals)
async def get_dietary_goals(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    goals = db.query(DietaryGoalsModel).filter(
        DietaryGoalsModel.owner_id == current_user.id
    ).first()
    if not goals:
        goals = DietaryGoalsModel(
            daily_calories=0,
            water_intake=0,
            owner_id=current_user.id
        )
        db.add(goals)
        db.commit()
        db.refresh(goals)
    return goals

@app.post("/health/recommendations")
async def get_recommendations(
    health_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Generate personalized health recommendations using LLM based on user's health data"""
    try:
        # Prepare the prompt for the LLM
        measurements = health_data.get('measurements', {})
        goals = health_data.get('goals', {})
        
        prompt = f"""Based on the following health data, provide 3 personalized health recommendations. Each recommendation should have a title, description, and 3 specific action items.

Current Health Measurements:
- BMI: {measurements.get('bmi', 'Not available')}
- Weight: {measurements.get('weight', 'Not available')} kg
- Height: {measurements.get('height', 'Not available')} cm
- Heart Rate: {measurements.get('heartRate', 'Not available')} bpm
- Blood Pressure: {measurements.get('bloodPressure', 'Not available')}

Health Goals:
- Daily Steps Target: {goals.get('dailySteps', 'Not set')}
- Weekly Exercise Minutes: {goals.get('weeklyExerciseMinutes', 'Not set')}
- Daily Calorie Target: {goals.get('dailyCalories', 'Not set')}
- Daily Water Intake Target: {goals.get('waterIntake', 'Not set')} L

Please provide recommendations in the following format for each:
1. Title: [Recommendation Title]
   Description: [2-3 sentences explaining the recommendation]
   Action Items:
   - [Specific action 1]
   - [Specific action 2]
   - [Specific action 3]
"""

        # Generate recommendations using LLM
        response = completion(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a knowledgeable health advisor providing personalized recommendations based on health data."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        # Parse LLM response into structured recommendations
        raw_recommendations = response.choices[0].message.content.strip().split('\n\n')
        recommendations = []
        
        for raw_rec in raw_recommendations:
            if not raw_rec.strip():
                continue
                
            lines = raw_rec.strip().split('\n')
            title = lines[0].replace('Title:', '').strip()
            description = lines[1].replace('Description:', '').strip()
            
            action_items = []
            for line in lines[3:]:
                if line.strip().startswith('-'):
                    action_items.append(line.strip('- ').strip())
            
            if title and description and action_items:
                recommendations.append({
                    "title": title,
                    "description": description,
                    "actionItems": action_items
                })

        return recommendations

    except Exception as e:
        logger.error(f"Error generating health recommendations: {str(e)}")
        logger.error(traceback.format_exc())
        # Fallback to static recommendations if LLM fails
        return [
            {
                "title": "Exercise Recommendation",
                "description": "Based on your activity level, try to increase your daily steps gradually.",
                "actionItems": [
                    "Take a 10-minute walk after each meal",
                    "Use stairs instead of elevator when possible",
                    "Park farther from entrances"
                ]
            },
            {
                "title": "Dietary Recommendation",
                "description": "Stay hydrated and maintain a balanced diet.",
                "actionItems": [
                    "Drink water before each meal",
                    "Include more vegetables in your meals",
                    "Track your daily calorie intake"
                ]
            },
            {
                "title": "Wellness Tip",
                "description": "Maintain good sleep hygiene for better health.",
                "actionItems": [
                    "Aim for 7-9 hours of sleep",
                    "Establish a regular sleep schedule",
                    "Avoid screens before bedtime"
                ]
            }
        ]

@app.post("/travel/trips", response_model=Trip)
async def create_trip(trip: TripCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    db_trip = TripModel(**trip.dict(), owner_id=current_user.id)
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip

@app.get("/travel/trips", response_model=List[Trip])
async def get_trips(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    trips = db.query(TripModel).filter(
        TripModel.owner_id == current_user.id
    ).order_by(TripModel.start_date.desc()).all()
    return trips

@app.get("/travel/trips/{trip_id}", response_model=Trip)
async def get_trip(trip_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    trip = db.query(TripModel).filter(
        TripModel.id == trip_id,
        TripModel.owner_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip

@app.post("/travel/accommodations", response_model=Accommodation)
async def create_accommodation(accommodation: AccommodationCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verify trip belongs to user
    trip = db.query(TripModel).filter(
        TripModel.id == accommodation.trip_id,
        TripModel.owner_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    db_accommodation = AccommodationModel(**accommodation.dict())
    db.add(db_accommodation)
    db.commit()
    db.refresh(db_accommodation)
    return db_accommodation

@app.post("/travel/flights", response_model=Flight)
async def create_flight(flight: FlightCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verify trip belongs to user
    trip = db.query(TripModel).filter(
        TripModel.id == flight.trip_id,
        TripModel.owner_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    db_flight = FlightModel(**flight.dict())
    db.add(db_flight)
    db.commit()
    db.refresh(db_flight)
    return db_flight

@app.post("/travel/car-rentals", response_model=CarRental)
async def create_car_rental(car_rental: CarRentalCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verify trip belongs to user
    trip = db.query(TripModel).filter(
        TripModel.id == car_rental.trip_id,
        TripModel.owner_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    db_car_rental = CarRentalModel(**car_rental.dict())
    db.add(db_car_rental)
    db.commit()
    db.refresh(db_car_rental)
    return db_car_rental

@app.get("/travel/trips/{trip_id}/details")
async def get_trip_details(trip_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    trip = db.query(TripModel).filter(
        TripModel.id == trip_id,
        TripModel.owner_id == current_user.id
    ).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    accommodations = db.query(AccommodationModel).filter(
        AccommodationModel.trip_id == trip_id
    ).all()
    
    flights = db.query(FlightModel).filter(
        FlightModel.trip_id == trip_id
    ).all()
    
    car_rentals = db.query(CarRentalModel).filter(
        CarRentalModel.trip_id == trip_id
    ).all()
    
    return {
        "trip": trip,
        "accommodations": accommodations,
        "flights": flights,
        "car_rentals": car_rentals
    }

@app.post("/travel/trips/{trip_id}/recommendations")
async def get_trip_recommendations(
    trip_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate personalized trip recommendations using LLM based on trip details"""
    try:
        # Get trip details
        trip = db.query(TripModel).filter(
            TripModel.id == trip_id,
            TripModel.owner_id == current_user.id
        ).first()
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")

        accommodations = db.query(AccommodationModel).filter(
            AccommodationModel.trip_id == trip_id
        ).all()
        
        flights = db.query(FlightModel).filter(
            FlightModel.trip_id == trip_id
        ).all()
        
        car_rentals = db.query(CarRentalModel).filter(
            CarRentalModel.trip_id == trip_id
        ).all()

        # Calculate trip duration
        duration_days = (trip.end_date - trip.start_date).days

        # Prepare the prompt for the LLM
        prompt = f"""Based on the following trip details, provide 3-4 personalized recommendations. Each recommendation should include activities, local attractions, or travel tips specific to the destination and timing of the trip.

Trip Details:
- Destination: {trip.destination}
- Duration: {duration_days} days ({trip.start_date.strftime('%B %d')} - {trip.end_date.strftime('%B %d, %Y')})
- Accommodations: {', '.join(acc.name for acc in accommodations) if accommodations else 'Not booked yet'}
- Transportation: {'Flights booked' if flights else 'No flights booked'}, {'Car rental arranged' if car_rentals else 'No car rental'}

Please provide recommendations in the following format:
1. Title: [Recommendation Title]
   Description: [2-3 sentences explaining the recommendation]
   Action Items:
   - [Specific action 1]
   - [Specific action 2]
   - [Specific action 3]

Focus on:
- Local attractions and activities
- Seasonal considerations for the travel dates
- Transportation and logistics tips
- Cultural experiences and local customs
- Safety and practical travel advice
"""

        # Generate recommendations using LLM
        response = completion(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a knowledgeable travel advisor providing personalized recommendations based on trip details."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        # Parse LLM response into structured recommendations
        raw_recommendations = response.choices[0].message.content.strip().split('\n\n')
        recommendations = []
        
        current_rec = {}
        current_action_items = []
        
        for line in response.choices[0].message.content.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith(('1.', '2.', '3.', '4.')):
                # Save previous recommendation if exists
                if current_rec and 'title' in current_rec:
                    current_rec['actionItems'] = current_action_items
                    recommendations.append(current_rec)
                    current_rec = {}
                    current_action_items = []
                continue
                
            if 'Title:' in line:
                current_rec['title'] = line.split('Title:', 1)[1].strip()
            elif 'Description:' in line:
                current_rec['description'] = line.split('Description:', 1)[1].strip()
            elif line.startswith('- '):
                current_action_items.append(line[2:].strip())
        
        # Add the last recommendation
        if current_rec and 'title' in current_rec:
            current_rec['actionItems'] = current_action_items
            recommendations.append(current_rec)

        # If no valid recommendations were parsed, create a default one
        if not recommendations:
            recommendations = [{
                "title": f"Explore {trip.destination}",
                "description": f"Discover the best of {trip.destination} during your {duration_days}-day trip.",
                "actionItems": [
                    "Research local attractions and create an itinerary",
                    "Check local weather and pack accordingly",
                    "Learn about local customs and basic phrases"
                ]
            }]

        return recommendations

    except Exception as e:
        logger.error(f"Error generating trip recommendations: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Return a default recommendation in case of error
        return [{
            "title": f"Explore {trip.destination}",
            "description": f"Discover the best of {trip.destination} during your {duration_days}-day trip.",
            "actionItems": [
                "Research local attractions and create an itinerary",
                "Check local weather and pack accordingly",
                "Learn about local customs and basic phrases"
            ]
        }]

@app.post("/weather/locations", response_model=WeatherLocation)
async def add_weather_location(
    location: WeatherLocationCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a new weather location for the current user"""
    try:
        # Validate location exists by trying to fetch its weather
        weather_data = await fetch_weather_data(location.name)
        if not weather_data:
            raise HTTPException(status_code=400, detail="Invalid location name")

        # Check if location already exists for user
        existing_location = db.query(WeatherLocationModel).filter(
            WeatherLocationModel.name == location.name,
            WeatherLocationModel.owner_id == current_user.id
        ).first()
        
        if existing_location:
            raise HTTPException(status_code=400, detail="Location already added")

        db_location = WeatherLocationModel(
            name=location.name,
            owner_id=current_user.id,
            current_temp=weather_data["current"]["temp"],
            last_updated=datetime.now()
        )
        db.add(db_location)
        db.commit()
        db.refresh(db_location)
        return db_location
    except Exception as e:
        logger.error(f"Error adding weather location: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/weather/locations", response_model=List[WeatherLocation])
async def get_weather_locations(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all weather locations for the current user"""
    locations = db.query(WeatherLocationModel).filter(
        WeatherLocationModel.owner_id == current_user.id
    ).all()
    return locations

@app.delete("/weather/locations/{location_id}")
async def remove_weather_location(
    location_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a weather location"""
    location = db.query(WeatherLocationModel).filter(
        WeatherLocationModel.id == location_id,
        WeatherLocationModel.owner_id == current_user.id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    db.delete(location)
    db.commit()
    return {"message": "Location removed successfully"}

@app.get("/weather/{location_id}")
async def get_weather_data(
    location_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weather data for a location"""
    location = db.query(WeatherLocationModel).filter(
        WeatherLocationModel.id == location_id,
        WeatherLocationModel.owner_id == current_user.id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Check cache first
    cache_key = f"weather_{location_id}"
    if cache_key in weather_cache:
        return weather_cache[cache_key]
    
    # Fetch new data if not in cache or expired
    weather_data = await fetch_weather_data(location.name)
    
    # Update location's current temperature and last updated time
    location.current_temp = weather_data["current"]["temp"]
    location.last_updated = datetime.now()
    db.commit()
    
    # Cache the result
    weather_cache[cache_key] = weather_data
    
    return weather_data

async def fetch_weather_data(location: str) -> dict:
    """Fetch weather data from OpenWeatherMap API with rate limiting and error handling"""
    default_weather_data = {
        "current": {
            "location": location,
            "temp": 20,
            "description": "Weather data unavailable",
            "high": 25,
            "low": 15,
            "wind_speed": 0,
            "precipitation": 0,
            "humidity": 50,
            "feels_like": 20,
            "pressure": 1013,
            "icon": "50d"
        },
        "hourly": [
            {
                "time": (datetime.now() + timedelta(hours=i)).isoformat(),
                "temp": 20,
                "precipitation": 0,
                "description": "Forecast unavailable",
                "icon": "50d"
            } for i in range(24)
        ],
        "daily": [
            {
                "date": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
                "high": 25,
                "low": 15,
                "precipitation": 0,
                "description": "Forecast unavailable",
                "icon": "50d"
            } for i in range(7)
        ]
    }

    try:
        # Validate API key
        if not OPENWEATHER_API_KEY:
            logger.error("OpenWeatherMap API key is missing")
            return default_weather_data

        async with aiohttp.ClientSession() as session:
            # Get coordinates for the location
            params = {
                "q": location,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric"
            }
            
            # Get current weather
            current_url = f"{WEATHER_API_BASE_URL}/weather"
            async with session.get(current_url, params=params) as response:
                if response.status == 401:
                    logger.error("Invalid OpenWeatherMap API key")
                    return default_weather_data
                elif response.status != 200:
                    logger.error(f"Failed to fetch current weather for {location}. Status: {response.status}")
                    error_data = await response.json()
                    logger.error(f"Error response: {error_data}")
                    return default_weather_data
                
                current_data = await response.json()
                
                # Get coordinates from current weather response
                lat = current_data["coord"]["lat"]
                lon = current_data["coord"]["lon"]
            
            # Get 5-day forecast
            forecast_url = f"{WEATHER_API_BASE_URL}/forecast"
            forecast_params = {
                "lat": lat,
                "lon": lon,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric"
            }
            
            async with session.get(forecast_url, params=forecast_params) as response:
                if response.status == 401:
                    logger.error("Invalid OpenWeatherMap API key for One Call API")
                    return default_weather_data
                elif response.status != 200:
                    logger.error(f"Failed to fetch forecast data for {location}. Status: {response.status}")
                    error_data = await response.json()
                    logger.error(f"Error response: {error_data}")
                    # Try using current weather data only if One Call API fails
                    return {
                        "current": {
                            "location": location,
                            "temp": round(current_data["main"]["temp"]),
                            "description": current_data["weather"][0]["description"],
                            "high": round(current_data["main"]["temp_max"]),
                            "low": round(current_data["main"]["temp_min"]),
                            "wind_speed": round(current_data["wind"]["speed"]),
                            "precipitation": 0,  # Not available in current weather
                            "humidity": current_data["main"]["humidity"],
                            "feels_like": round(current_data["main"]["feels_like"]),
                            "pressure": current_data["main"]["pressure"],
                            "icon": current_data["weather"][0]["icon"],
                            "locationId": current_data.get("id")
                        },
                        "hourly": [default_weather_data["hourly"][0]],  # Use default hourly data
                        "daily": [default_weather_data["daily"][0]]  # Use default daily data
                    }
                
                forecast_data = await response.json()

                # Process the 5-day forecast data
                hourly_forecasts = []
                daily_forecasts = {}
                
                for item in forecast_data["list"]:
                    dt = datetime.fromtimestamp(item["dt"])
                    
                    # Add to hourly forecasts (first 24 entries)
                    if len(hourly_forecasts) < 24:
                        hourly_forecasts.append({
                            "time": dt.isoformat(),
                            "temp": round(item["main"]["temp"]),
                            "precipitation": item.get("pop", 0) * 100,
                            "description": item["weather"][0]["description"],
                            "icon": item["weather"][0]["icon"]
                        })
                    
                    # Group by date for daily forecasts
                    date_key = dt.strftime("%Y-%m-%d")
                    if date_key not in daily_forecasts:
                        daily_forecasts[date_key] = {
                            "date": date_key,
                            "high": round(item["main"]["temp_max"]),
                            "low": round(item["main"]["temp_min"]),
                            "precipitation": item.get("pop", 0) * 100,
                            "description": item["weather"][0]["description"],
                            "icon": item["weather"][0]["icon"]
                        }
                    else:
                        # Update high/low temperatures
                        daily_forecasts[date_key]["high"] = max(daily_forecasts[date_key]["high"], round(item["main"]["temp_max"]))
                        daily_forecasts[date_key]["low"] = min(daily_forecasts[date_key]["low"], round(item["main"]["temp_min"]))
                        daily_forecasts[date_key]["precipitation"] = max(daily_forecasts[date_key]["precipitation"], item.get("pop", 0) * 100)

                # Format the response
                return {
                    "current": {
                        "location": location,
                        "temp": round(current_data["main"]["temp"]),
                        "description": current_data["weather"][0]["description"],
                        "high": round(current_data["main"]["temp_max"]),
                        "low": round(current_data["main"]["temp_min"]),
                        "wind_speed": round(current_data["wind"]["speed"]),
                        "precipitation": forecast_data["list"][0].get("pop", 0) * 100 if forecast_data["list"] else 0,
                        "humidity": current_data["main"]["humidity"],
                        "feels_like": round(current_data["main"]["feels_like"]),
                        "pressure": current_data["main"]["pressure"],
                        "icon": current_data["weather"][0]["icon"],
                        "locationId": current_data.get("id")
                    },
                    "hourly": hourly_forecasts,
                    "daily": list(daily_forecasts.values())[:7]  # Get first 7 days
                }
    except Exception as e:
        logger.error(f"Error fetching weather data for {location}: {str(e)}")
        logger.error(traceback.format_exc())
        return default_weather_data

@app.get("/weather/{location_id}/recommendations")
async def get_weather_recommendations(
    location_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get clothing and home temperature recommendations based on weather data"""
    try:
        # First try to get location by database ID
        location = db.query(WeatherLocationModel).filter(
            WeatherLocationModel.id == location_id,
            WeatherLocationModel.owner_id == current_user.id
        ).first()
        
        # If not found by database ID, try to find by OpenWeatherMap location ID
        if not location:
            location = db.query(WeatherLocationModel).filter(
                WeatherLocationModel.owner_id == current_user.id
            ).all()
            # Find location by checking weather data for each location
            for loc in location:
                weather_data = await fetch_weather_data(loc.name)
                if weather_data.get("current", {}).get("locationId") == location_id:
                    location = loc
                    break
        
        if not location:
            logger.error(f"Location {location_id} not found for user {current_user.id}")
            return {
                "clothing": {
                    "whatToWear": ["Unable to provide recommendations - location not found"],
                    "specialItems": [],
                    "tips": ["Please add a valid location to get weather-based recommendations"]
                },
                "homeTemperature": {
                    "recommendedTemp": 21,
                    "energySavingTips": ["Add a location to get personalized temperature recommendations"],
                    "comfortTips": []
                }
            }
            
        # Get weather data using location name
        weather_data = await fetch_weather_data(location.name)
        
        # Prepare the prompt for the LLM
        prompt = f"""Based on the following weather conditions, provide recommendations for clothing and home temperature settings. Include specific suggestions for comfort and energy efficiency.

Current Weather Conditions:
- Temperature: {weather_data['current']['temp']}°C
- Feels Like: {weather_data['current']['feels_like']}°C
- Weather: {weather_data['current']['description']}
- Humidity: {weather_data['current']['humidity']}%
- Wind Speed: {weather_data['current']['wind_speed']} m/s

Today's Forecast:
- High: {weather_data['current']['high']}°C
- Low: {weather_data['current']['low']}°C
- Precipitation Chance: {weather_data['current']['precipitation']}%

Please provide recommendations in the following format:

1. Clothing Recommendations:
   - What to Wear: [List of recommended clothing items]
   - Special Items: [Any special items needed based on weather]
   - Tips: [Additional clothing-related advice]

2. Home Temperature Settings:
   - Recommended Temperature: [Temperature setting in Celsius]
   - Energy Saving Tips: [List of energy-saving suggestions]
   - Additional Comfort Tips: [Other comfort-related recommendations]
"""

        # Generate recommendations using LLM
        response = completion(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a knowledgeable advisor providing practical recommendations for clothing and home temperature settings based on weather conditions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )

        # Parse LLM response into structured recommendations
        recommendations = {
            "clothing": {
                "whatToWear": [],
                "specialItems": [],
                "tips": []
            },
            "homeTemperature": {
                "recommendedTemp": None,
                "energySavingTips": [],
                "comfortTips": []
            }
        }

        current_section = None
        current_subsection = None

        for line in response.choices[0].message.content.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            if "Clothing Recommendations:" in line:
                current_section = "clothing"
                continue
            elif "Home Temperature Settings:" in line:
                current_section = "homeTemperature"
                continue

            if line.startswith("- What to Wear:"):
                current_subsection = "whatToWear"
                items = line.split(":", 1)[1].strip()
                recommendations["clothing"]["whatToWear"] = [item.strip() for item in items.split(",")]
            elif line.startswith("- Special Items:"):
                current_subsection = "specialItems"
                items = line.split(":", 1)[1].strip()
                recommendations["clothing"]["specialItems"] = [item.strip() for item in items.split(",")]
            elif line.startswith("- Tips:"):
                current_subsection = "tips"
                items = line.split(":", 1)[1].strip()
                recommendations["clothing"]["tips"] = [item.strip() for item in items.split(",")]
            elif line.startswith("- Recommended Temperature:"):
                temp_str = line.split(":", 1)[1].strip()
                try:
                    # Extract the numeric temperature value
                    temp = float(''.join(filter(str.isdigit, temp_str)))
                    recommendations["homeTemperature"]["recommendedTemp"] = temp
                except ValueError:
                    recommendations["homeTemperature"]["recommendedTemp"] = 21  # Default temperature if parsing fails
            elif line.startswith("- Energy Saving Tips:"):
                current_subsection = "energySavingTips"
                items = line.split(":", 1)[1].strip()
                recommendations["homeTemperature"]["energySavingTips"] = [item.strip() for item in items.split(",")]
            elif line.startswith("- Additional Comfort Tips:"):
                current_subsection = "comfortTips"
                items = line.split(":", 1)[1].strip()
                recommendations["homeTemperature"]["comfortTips"] = [item.strip() for item in items.split(",")]
            elif line.startswith("- ") and current_section and current_subsection:
                item = line[2:].strip()
                if current_section == "clothing":
                    recommendations[current_section][current_subsection].append(item)
                elif current_section == "homeTemperature":
                    recommendations[current_section][current_subsection].append(item)

        return recommendations

    except Exception as e:
        logger.error(f"Error generating weather recommendations: {str(e)}")
        logger.error(traceback.format_exc())
        # Return default recommendations in case of error
        return {
            "clothing": {
                "whatToWear": ["Comfortable clothing appropriate for the season"],
                "specialItems": ["Check weather conditions before going out"],
                "tips": ["Layer clothing for flexibility"]
            },
            "homeTemperature": {
                "recommendedTemp": 21,
                "energySavingTips": [
                    "Use programmable thermostat",
                    "Seal any drafts",
                    "Regular HVAC maintenance"
                ],
                "comfortTips": [
                    "Adjust temperature gradually",
                    "Consider humidity levels",
                    "Use fans to circulate air"
                ]
            }
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
