"""Dashboard API Router - Oceanographic data visualization and metrics"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
import os
import math
import psycopg2
from psycopg2.extras import RealDictCursor

# Add paths for importing existing services
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.dirname(current_dir)
app_dir = os.path.dirname(api_dir)
backend_dir = os.path.dirname(app_dir)

sys.path.insert(0, backend_dir)
sys.path.insert(0, app_dir)
sys.path.insert(0, api_dir)

router = APIRouter()

# Database connection configuration
DB_CONFIG = {
    "dbname": "indian_ocean",
    "user": "pawani",
    "password": "pawani09",
    "host": "20.244.12.11",
    "port": "5432"
}
def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print(f"✓ Successfully connected to database: {DB_CONFIG['dbname']}")
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print(f"   Attempted to connect to: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        print(f"   Database: {DB_CONFIG['dbname']}, User: {DB_CONFIG['user']}")
        print(f"   ⚠️  Using mock data instead of live database")
        raise e

def get_mock_db_connection():
    """Mock database connection that returns mock data when real database is unavailable"""
    print("📊 Using mock database data for dashboard")
    return None

def is_valid_number(value):
    """Check if a value is a valid number (not NaN or infinite)"""
    if value is None:
        return False
    try:
        float_val = float(value)
        return not (math.isnan(float_val) or math.isinf(float_val))
    except (ValueError, TypeError):
        return False

# Response Models
class MetricsResponse(BaseModel):
    total_floats: int
    active_floats: int
    total_profiles: int

class ParametersMetricsResponse(BaseModel):
    avg_surface_temp: float
    avg_surface_salinity: float

class FloatInfo(BaseModel):
    id: str
    lat: float
    lon: float
    data_mode: str

class TrajectoryResponse(BaseModel):
    trajectory: List[Dict]
    platform_number: str
    total_points: int
    message: Optional[str] = None

class TimeSeriesResponse(BaseModel):
    data: List[Dict]
    platform_number: str
    variable: str
    total_points: int
    message: Optional[str] = None

class FloatDetailResponse(BaseModel):
    id: str
    lat: float
    lon: float
    data_mode: str

class TsDiagramResponse(BaseModel):
    profile_id: int
    data: List[Dict]
    total_points: int

@router.get("/metrics", response_model=MetricsResponse)
def get_metrics():
    """Get dashboard metrics including total floats, active floats, and total profiles"""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query for metrics
        query = """
            SELECT 
                COUNT(DISTINCT platform_number) AS active_floats
            FROM profiles
            WHERE data_mode IN ('R', 'A')
        """
        cur.execute(query)
        active_floats = cur.fetchone()['active_floats']

        query = """
            SELECT 
                COUNT(DISTINCT platform_number) AS total_floats
            FROM profiles
        """
        cur.execute(query)
        total_floats = cur.fetchone()['total_floats']
        if total_floats is None:
            total_floats = 0
        
        query = """
            SELECT
                COUNT(*) AS total_profiles
            FROM profiles
        """
        cur.execute(query)
        total_profiles = cur.fetchone()['total_profiles']
        if total_profiles is None:
            total_profiles = 0

        return {
            "total_floats": total_floats,
            "active_floats": active_floats,
            "total_profiles": total_profiles
        }
    except psycopg2.OperationalError as e:
        # Database connection failed, return mock data
        print("📊 Returning mock metrics data")
        return {
            "total_floats": 3847,
            "active_floats": 2156,
            "total_profiles": 2450000
        }
    except ValueError as e:
        return JSONResponse({"error": "Invalid date format. Use DD-MM-YYYY"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/parameters/metrics", response_model=ParametersMetricsResponse)
def get_parameters_metrics(year: int = Query(..., description="Year in YYYY format")):
    """Get parameter metrics including average surface temperature and salinity for a specific year"""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Query for parameters metrics
        query = f"""
            SELECT AVG(pl.temp) AS avg_surface_temp
            FROM profiles p
            JOIN profile_levels pl ON pl.profile_id = p.id
            WHERE EXTRACT(YEAR FROM p.juld) = {year}
            AND pl.level = 0
            AND pl.temp IS NOT NULL
            AND pl.temp != 'NaN';
        """
        cur.execute(query)
        avg_surface_temp = cur.fetchone()['avg_surface_temp']

        query = f"""
            SELECT AVG(pl.psal) AS avg_surface_salinity
            FROM profiles p
            JOIN profile_levels pl ON pl.profile_id = p.id
            WHERE EXTRACT(YEAR FROM p.juld) = {year}
            AND pl.level = 0
            AND pl.psal IS NOT NULL
        """
        cur.execute(query)
        avg_surface_salinity = cur.fetchone()['avg_surface_salinity']

        return {
            "avg_surface_temp": round(avg_surface_temp, 2),
            "avg_surface_salinity": round(avg_surface_salinity, 2)
        }
    except ValueError as e:
        return JSONResponse({"error": "Invalid date format. Use DD-MM-YYYY"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/floats", response_model=List[FloatInfo])
def get_floats():
    """Get list of all active floats with their positions and data modes"""
    conn = None
    cur = None
    try:
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT DISTINCT ON (platform_number) platform_number, latitude, longitude, data_mode
            FROM profiles
            WHERE data_mode IN ('R', 'A')
            ORDER BY platform_number DESC
        """
        cur.execute(query)
        floats = cur.fetchall()

        return [{"id": f['platform_number'], "lat": f['latitude'], "lon": f['longitude'], "data_mode": f['data_mode']} for f in floats]
    except psycopg2.OperationalError as e:
        # Database connection failed, return mock data
        print("📊 Returning mock floats data")
        return [
            {"id": "2901234", "lat": -8.5, "lon": 78.2, "data_mode": "R"},
            {"id": "2901235", "lat": -12.3, "lon": 82.1, "data_mode": "R"},
            {"id": "2901236", "lat": -15.7, "lon": 75.8, "data_mode": "A"},
            {"id": "2901237", "lat": -20.1, "lon": 88.5, "data_mode": "R"},
            {"id": "2901238", "lat": -25.4, "lon": 72.3, "data_mode": "A"},
            {"id": "2901239", "lat": -30.2, "lon": 85.7, "data_mode": "R"},
            {"id": "2901240", "lat": -35.8, "lon": 78.9, "data_mode": "R"},
            {"id": "2901241", "lat": -40.5, "lon": 92.1, "data_mode": "A"}
        ]
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/trajectory/{platform_number}", response_model=TrajectoryResponse)
def get_trajectory(platform_number: str):
    """Get trajectory data for a specific float platform number"""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get trajectory points for the specific platform ordered by date
        query = """
            SELECT latitude, longitude, juld as date
            FROM profiles 
            WHERE platform_number = %s 
            AND latitude IS NOT NULL 
            AND longitude IS NOT NULL
            ORDER BY juld ASC
        """
        cur.execute(query, (platform_number,))
        trajectory_points = cur.fetchall()
        
        if not trajectory_points:
            return {
                "trajectory": [], 
                "platform_number": platform_number, 
                "message": "No trajectory data found"
            }
        
        trajectory_data = []
        for point in trajectory_points:
            trajectory_data.append({
                "lat": float(point['latitude']),
                "lon": float(point['longitude']),
                "date": point['date'].isoformat() if point['date'] else None
            })
        
        return {
            "trajectory": trajectory_data,
            "platform_number": platform_number,
            "total_points": len(trajectory_data)
        }
    except psycopg2.OperationalError as e:
        # Database connection failed, return mock data
        print(f"📊 Returning mock trajectory data for float {platform_number}")
        mock_trajectory = [
            {"lat": -8.5, "lon": 78.2, "date": "2023-01-15T00:00:00"},
            {"lat": -9.2, "lon": 78.8, "date": "2023-02-20T00:00:00"},
            {"lat": -10.1, "lon": 79.5, "date": "2023-03-25T00:00:00"},
            {"lat": -11.3, "lon": 80.2, "date": "2023-04-30T00:00:00"},
            {"lat": -12.7, "lon": 81.0, "date": "2023-06-05T00:00:00"},
            {"lat": -14.2, "lon": 81.8, "date": "2023-07-10T00:00:00"},
            {"lat": -15.8, "lon": 82.5, "date": "2023-08-15T00:00:00"},
            {"lat": -17.5, "lon": 83.2, "date": "2023-09-20T00:00:00"},
            {"lat": -19.1, "lon": 83.9, "date": "2023-10-25T00:00:00"},
            {"lat": -20.7, "lon": 84.6, "date": "2023-11-30T00:00:00"},
            {"lat": -22.3, "lon": 85.3, "date": "2023-12-15T00:00:00"}
        ]
        return {
            "trajectory": mock_trajectory,
            "platform_number": platform_number,
            "total_points": len(mock_trajectory),
            "message": "Mock data (database unavailable)"
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/time_series/{platform_number}", response_model=TimeSeriesResponse)
def get_time_series_data(platform_number: str, variable: str = Query("temp", description="Variable to plot: temp or psal")):
    """Get time series data for surface measurements (temperature or salinity) for a specific float"""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get time series data for surface measurements (level=0)
        query = """
            SELECT
                p.juld AS date,
                pl.temp,
                pl.psal
            FROM
                profiles AS p
            JOIN
                profile_levels AS pl ON p.id = pl.profile_id
            WHERE
                p.platform_number = %s
                AND pl.level = 0
                AND p.juld IS NOT NULL
            ORDER BY
                p.juld ASC
        """
        cur.execute(query, (platform_number,))
        time_series_data = cur.fetchall()

        if not time_series_data:
            return {
                "data": [], 
                "platform_number": platform_number, 
                "variable": variable,
                "message": "No time series data found"
            }
        
        # Filter out null/NaN values for the selected variable
        filtered_data = []
        for point in time_series_data:
            # Check if the selected variable has a valid value
            if is_valid_number(point[variable]):
                filtered_data.append({
                    "date": point['date'].isoformat() if point['date'] else None,
                    "temp": float(point['temp']) if is_valid_number(point['temp']) else None,
                    "psal": float(point['psal']) if is_valid_number(point['psal']) else None,
                    "value": float(point[variable])
                })
        
        return {
            "data": filtered_data,
            "platform_number": platform_number,
            "variable": variable,
            "total_points": len(filtered_data)
        }
    except psycopg2.OperationalError as e:
        # Database connection failed, return mock data
        print(f"📊 Returning mock time series data for float {platform_number}")
        mock_time_series = [
            {"date": "2023-01-15T00:00:00", "temp": 26.5, "psal": 35.1, "value": 26.5 if variable == 'temp' else 35.1},
            {"date": "2023-02-20T00:00:00", "temp": 27.2, "psal": 35.3, "value": 27.2 if variable == 'temp' else 35.3},
            {"date": "2023-03-25T00:00:00", "temp": 27.8, "psal": 35.2, "value": 27.8 if variable == 'temp' else 35.2},
            {"date": "2023-04-30T00:00:00", "temp": 28.1, "psal": 35.4, "value": 28.1 if variable == 'temp' else 35.4},
            {"date": "2023-06-05T00:00:00", "temp": 27.9, "psal": 35.5, "value": 27.9 if variable == 'temp' else 35.5},
            {"date": "2023-07-10T00:00:00", "temp": 27.4, "psal": 35.3, "value": 27.4 if variable == 'temp' else 35.3},
            {"date": "2023-08-15T00:00:00", "temp": 26.8, "psal": 35.2, "value": 26.8 if variable == 'temp' else 35.2},
            {"date": "2023-09-20T00:00:00", "temp": 26.3, "psal": 35.1, "value": 26.3 if variable == 'temp' else 35.1},
            {"date": "2023-10-25T00:00:00", "temp": 25.9, "psal": 35.0, "value": 25.9 if variable == 'temp' else 35.0},
            {"date": "2023-11-30T00:00:00", "temp": 25.5, "psal": 34.9, "value": 25.5 if variable == 'temp' else 34.9},
            {"date": "2023-12-15T00:00:00", "temp": 25.2, "psal": 34.8, "value": 25.2 if variable == 'temp' else 34.8}
        ]
        return {
            "data": mock_time_series,
            "platform_number": platform_number,
            "variable": variable,
            "total_points": len(mock_time_series),
            "message": "Mock data (database unavailable)"
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/float/{float_id}", response_model=FloatDetailResponse)
async def get_specific_float(float_id: str):
    """Get detailed information for a specific float by ID"""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query for the specific float details
        query = """
            SELECT platform_number, latitude, longitude, data_mode
            FROM profiles
            WHERE platform_number = %s
        """
        cur.execute(query, (float_id,))
        float_data = cur.fetchone()

        if not float_data:
            return JSONResponse({"error": "Float not found"}, status_code=404)

        return {
            "id": float_data['platform_number'],
            "lat": float_data['latitude'],
            "lon": float_data['longitude'],
            "data_mode": float_data['data_mode']
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/ts_diagram/{profile_id}", response_model=TsDiagramResponse)
async def get_ts_diagram_data(profile_id: int):
    """Get Temperature-Salinity diagram data for a specific profile"""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query to get T-S data for a specific profile
        query = """
            SELECT 
                pl.temp AS temperature,
                pl.psal AS salinity,
                pl.pres AS depth,
                p.latitude,
                p.longitude
            FROM profile_levels pl
            JOIN profiles p ON pl.profile_id = p.id
            WHERE pl.profile_id = %s
            AND pl.temp IS NOT NULL 
            AND pl.psal IS NOT NULL
            AND pl.temp != 'NaN'
            AND pl.psal != 'NaN'
            ORDER BY pl.pres
        """
        
        cur.execute(query, (profile_id,))
        ts_data = cur.fetchall()
        
        if not ts_data:
            return JSONResponse({"error": "No T-S data found for this profile"}, status_code=404)
        
        # Format data for frontend
        formatted_data = []
        for point in ts_data:
            if is_valid_number(point['temperature']) and is_valid_number(point['salinity']):
                formatted_data.append({
                    "temperature": round(float(point['temperature']), 3),
                    "salinity": round(float(point['salinity']), 3),
                    "depth": round(float(point['depth']), 1),
                    "latitude": float(point['latitude']) if point['latitude'] else None,
                    "longitude": float(point['longitude']) if point['longitude'] else None
                })
        
        return {
            "profile_id": profile_id,
            "data": formatted_data,
            "total_points": len(formatted_data)
        }
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
