from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import models
from pydantic import BaseModel

# Create FastAPI app
app = FastAPI(title="NHC Storm Tracker API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class StormBase(BaseModel):
    id: int
    storm_id: str
    storm_name: str
    storm_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    movement: Optional[str] = None
    wind_speed: Optional[int] = None
    pressure: Optional[int] = None
    headline: Optional[str] = None
    report: Optional[str] = None
    report_link: Optional[str] = None
    report_date: Optional[datetime] = None
    wallet: Optional[str] = None
    wallet_url: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StormResponse(BaseModel):
    success: bool
    data: StormBase

class StormsResponse(BaseModel):
    success: bool
    count: int
    data: List[StormBase]

# Dependency to get DB session
def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Endpoints
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "NHC Storm Tracker API",
        "endpoints": {
            "active_storms": "/api/v1/storms/active",
            "all_storms": "/api/v1/storms?season={year}&status={status}&storm_type={type}&min_wind_speed={speed}",
            "storm_by_id": "/api/v1/storms/{storm_id}",
            "storm_by_name": "/api/v1/storms/name/{storm_name}"
        },
        "filters": {
            "season": "Optional. Filter by storm season (year). Defaults to current year if not specified.",
            "status": "Optional. Filter by storm status (active/inactive).",
            "storm_type": "Optional. Filter by storm type (e.g., HURRICANE, TROPICAL STORM).",
            "min_wind_speed": "Optional. Filter by minimum wind speed in MPH."
        }
    }

@app.get("/api/v1/storms/active", response_model=StormsResponse, tags=["Storms"])
async def get_active_storms(
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
):
    """Get all active storms"""
    storms = db.query(models.Storm)\
        .filter(models.Storm.status == "active")\
        .order_by(models.Storm.updated_at.desc())\
        .limit(limit)\
        .all()
    return {
        "success": True,
        "count": len(storms),
        "data": storms
    }

@app.get("/api/v1/storms", response_model=StormsResponse, tags=["Storms"])
async def get_all_storms(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    season: Optional[int] = None,
    storm_type: Optional[str] = None,
    min_wind_speed: Optional[int] = None,
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip")
):
    """Get all storms with optional filters for status, season, type, and wind speed"""
    query = db.query(models.Storm)
    
    # Apply filters if provided
    if status:
        query = query.filter(models.Storm.status == status)
    
    # Filter by season if provided, otherwise use current year
    current_year = datetime.now().year
    if season:
        query = query.filter(models.Storm.season == season)
    else:
        query = query.filter(models.Storm.season == current_year)
    
    # Additional filters
    if storm_type:
        query = query.filter(models.Storm.storm_type.ilike(f"%{storm_type}%"))
    
    if min_wind_speed:
        query = query.filter(models.Storm.wind_speed >= min_wind_speed)
    
    total = query.count()
    storms = query.order_by(models.Storm.updated_at.desc())\
                    .offset(offset)\
                    .limit(limit)\
                    .all()
    
    return {
        "success": True,
        "count": total,
        "data": storms
    }

@app.get("/api/v1/storms/{storm_id}", response_model=StormResponse, tags=["Storms"])
async def get_storm_by_id(storm_id: str, db: Session = Depends(get_db)):
    """Get storm by ID"""
    storm = db.query(models.Storm).filter(models.Storm.storm_id == storm_id).first()
    if not storm:
        raise HTTPException(status_code=404, detail="Storm not found")
    return {"success": True, "data": storm}

@app.get("/api/v1/storms/name/{storm_name}", response_model=StormsResponse, tags=["Storms"])
async def get_storm_by_name(
    storm_name: str,
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
):
    """Get storms by name (case-insensitive)"""
    storms = db.query(models.Storm)\
        .filter(models.Storm.storm_name.ilike(f"%{storm_name}%"))\
        .order_by(models.Storm.updated_at.desc())\
        .limit(limit)\
        .all()
    
    if not storms:
        raise HTTPException(status_code=404, detail="No storms found with that name")
    
    return {
        "success": True,
        "count": len(storms),
        "data": storms
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
