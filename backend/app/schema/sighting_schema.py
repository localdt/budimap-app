 # Esquemas Pydantic
from pydantic import BaseModel
from typing import TypeVar, Optional, List
from fastapi import UploadFile, File
from datetime import date, datetime, time, timedelta

T = TypeVar('T')

class Response(BaseModel):
    detail: str
    result: Optional[T] = None
    
class FileBase(BaseModel):
    name: str
    path: str
    status: str
    sighting_id: int

class FileCreate(FileBase):
    name: str
    path: str
    status: str
    sighting_id: int
    ml_class_result: Optional[str] = None
    
class FileUpdate(BaseModel):
    status: str
    ml_class_result: Optional[str] = None
    
class SightingFile(FileBase):
    id: int
    ml_class_result: Optional[str] = None
    created: datetime = None

    class Config:
        orm_mode = True
    
class SightingBase(BaseModel):
    longitude: float
    latitude: float
    created: datetime = None

class SightingCreate(SightingBase):    
    status: str

class Sighting(SightingBase):
    id: int
    status: str

    class Config:
        orm_mode = True

class SightingForm(BaseModel):
    longitude: float
    latitude: float
    files: List[UploadFile] = File(...)
