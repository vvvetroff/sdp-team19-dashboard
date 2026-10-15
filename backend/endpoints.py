import os
from datetime import datetime, timedelta

import httpx

OWL_API_KEY: str | None = os.getenv('OWL_API_KEY')
OWL_INSTANCE: str | None = os.getenv('OWL_INSTANCE')

class RedisOpertations:
    def __init__(self, redis_client):
        self.redis_client = redis_client

    async def get_metrics_per_duck(self, device_id):
        metrics = self.redis_client.keys(f"{device_id}:*")
        return {device_id: metrics}

    async def get_values_of_metric_per_duck(self, device_id, metric):
        key = f"{device_id}:{metric}"
        values = self.redis_client.lrange(key, 0, -1)
        return {key: values}

    async def health(self):
        health = self.redis_client.ping()
        return {"health": health}

    async def get_all_ducks(self):
        ducks = self.redis_client.keys("*:*")
        result = set()
        for d in ducks:
            result.add(d.split(":")[0])
        
        return {"ducks": list(result)}
    
async def get_all_ducks_in_serial() -> dict[str, list[str]]:
    return {"ducks": list("1")}

async def get_all_ducks_in_dms() -> dict[str, list[str]]:
    url = f"http://{OWL_INSTANCE}/public_api/Data"
    headers = { 
        "accept": "application/json", 
        "X-API-Key": OWL_API_KEY
        }
    params = {
        "startDate": int((datetime.now() - timedelta(seconds=1)).timestamp())
        }
    
    async with httpx.AsyncClient() as client:
        response = await client.request(method="GET", url=url, headers=headers, params=params)
        _ = response.raise_for_status()
        data = response.json()
        if not data: raise Exception("No ducks available")
        ducks = set()
        for record in data:
            payload = record.get('payload')
            device_id = payload.get('DeviceID')
            ducks.add(device_id)

        return {"ducks": list(ducks)}
