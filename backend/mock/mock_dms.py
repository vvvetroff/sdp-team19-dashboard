# mock_owl_dms.py
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import Optional, Any
from dotenv import load_dotenv
import random
import uvicorn
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock API key for testing
load_dotenv()
VALID_API_KEY = os.getenv('OWL_API_KEY')

def generate_mock_message() -> dict[str, Any]:
    """Generate a realistic mock message matching OWL API format"""
    now = datetime.now()
    
    return {
        "deviceId": "PAPADUCK",
        "timestamp": now.isoformat() + "Z",
        "eventType": "health",
        "payload": {
            "hops": random.randint(1, 3),
            "Payload": {
                # Add more CAN fields as needed
                "Pack Voltage": round(random.uniform(0, 50), 2),
                "Pack Current": round(random.uniform(0, 50), 2),
                "Pack Temp": round(random.uniform(0, 50), 2),
                "State of Charge": round(random.uniform(0, 50), 2),
                "Min Cell Voltage": round(random.uniform(0, 50), 2),
                "BMS LV Input": round(random.uniform(0, 50), 2),
                "Torque Feedback": round(random.uniform(0, 50), 2),
                "RPM": round(random.uniform(0, 50), 2),
                "Flux Feedback": round(random.uniform(0, 50), 2),
            },
            "DeviceID": "DUCK0001",
            "duckType": 1,
            "MessageID": ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=4))
        }
    }


@app.get("/public_api/Data")
async def get_data(
    startDate: int = Query(..., description="Unix timestamp in seconds"),
    endDate: Optional[int] = Query(None, description="Unix timestamp in seconds (optional)"),
    x_api_key: str = Header(None, alias="X-API-Key")
) -> list[dict[str, Any]]:
    """
    Mock OWL API endpoint
    Returns messages generated since startDate
    Matches the exact response format from OWL's API
    
    Parameters:
    - startDate: Unix timestamp in seconds (int)
    - endDate: Unix timestamp in seconds (int, optional)
    """
    # Validate API key
    if x_api_key != VALID_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    try:
        # Convert Unix timestamps (in seconds) to datetime
        start_dt = datetime.fromtimestamp(startDate)
        end_dt = datetime.fromtimestamp(endDate) if endDate else datetime.now()
        
        print(f"Request: startDate={startDate} ({start_dt}), endDate={endDate} ({end_dt})")
        
    except (ValueError, OSError, OverflowError) as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid timestamp. Must be Unix timestamp in seconds. Error: {str(e)}"
        )
    
    # Generate messages for the time range
    time_diff = (end_dt - start_dt).total_seconds()
    
    if time_diff < 0:
        raise HTTPException(status_code=400, detail="endDate must be after startDate")
    
    num_messages = int(time_diff * 10)
    
    # Cap at reasonable number for testing
    num_messages = 1
    
    messages = []
    for i in range(num_messages):
        msg = generate_mock_message()
        # Adjust timestamp to be within range
        offset = timedelta(seconds=i * 0.1)  # 100ms apart
        msg_time = start_dt + offset
        msg["timestamp"] = msg_time.isoformat() + "Z"
        messages.append(msg)
    
    print(f"Returning {len(messages)} messages from {start_dt} to {end_dt}")
    return messages


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "Mock OWL DMS"}

if __name__ == "__main__":
    print("=" * 50)
    print("Mock OWL DMS API Server")
    print("=" * 50)
    print(f"API Key: {VALID_API_KEY}")
    print(f"Endpoint: http://localhost:5000/public_api/Data")
    print(f"Example: http://localhost:5000/public_api/Data?startDate={int(datetime.now().timestamp())}")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=5000)
