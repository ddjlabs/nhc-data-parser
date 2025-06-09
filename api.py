from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc
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
    season: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class StormHistoryBase(BaseModel):
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
    report_date: Optional[datetime] = None
    status: str
    season: int
    recorded_at: datetime
    
    class Config:
        from_attributes = True

class StormResponse(BaseModel):
    success: bool
    data: StormBase

class StormsResponse(BaseModel):
    success: bool
    count: int
    data: List[StormBase]
    
class StormHistoryResponse(BaseModel):
    success: bool
    count: int
    data: List[StormHistoryBase]

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
        "success": True,
        "message": "Welcome to the NHC Storm Tracker API",
        "endpoints": {
            "/api/v1/storms/active": "Get all active storms",
            "/api/v1/storms": "Get all storms with optional filters (status, season, type, min_wind_speed)",
            "/api/v1/storms/{storm_id}": "Get storm by ID",
            "/api/v1/storms/{storm_id}/history": "Get historical data for a specific storm",
            "/api/v1/storms/name/{storm_name}": "Search storms by name"
        },
        "examples": {
            "Get active storms": "/api/v1/storms/active",
            "Get all storms from 2023": "/api/v1/storms?season=2023",
            "Get all hurricanes": "/api/v1/storms?storm_type=HURRICANE",
            "Get storms with wind speed > 100 MPH": "/api/v1/storms?min_wind_speed=100",
            "Get history for a storm": "/api/v1/storms/EP022025/history"
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
    # Convert to lowercase for case-insensitive search
    storm_name_lower = storm_name.lower()
    
    # Query storms with name containing the search term (case-insensitive)
    storms = db.query(models.Storm).filter(
        models.Storm.storm_name.ilike(f"%{storm_name_lower}%")
    ).order_by(
        models.Storm.season.desc(),
        models.Storm.report_date.desc()
    ).limit(limit).all()
    
    if not storms:
        raise HTTPException(status_code=404, detail=f"No storms found with name containing '{storm_name}'")
    
    return {
        "success": True,
        "count": len(storms),
        "data": storms
    }

@app.get("/api/v1/storms/{storm_id}/history", response_model=StormHistoryResponse, tags=["Storms"])
async def get_storm_history(
    storm_id: str,
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip")
):
    """Get historical data for a specific storm"""
    # Check if storm exists
    storm = db.query(models.Storm).filter(models.Storm.storm_id == storm_id).first()
    if not storm:
        raise HTTPException(status_code=404, detail=f"Storm with ID '{storm_id}' not found")
    
    # Query storm history records
    history = db.query(models.StormHistory).filter(
        models.StormHistory.storm_id == storm_id
    ).order_by(
        desc(models.StormHistory.recorded_at)
    ).offset(offset).limit(limit).all()
    
    if not history:
        raise HTTPException(status_code=404, detail=f"No history records found for storm '{storm_id}'")
    
    return {
        "success": True,
        "count": len(history),
        "data": history
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
