import asyncio
import os
import json
from typing import Any
from datetime import datetime, timedelta

import httpx
import redis
import serial
from dotenv import load_dotenv

from helpers import println
from websocket_management import ConnectionManager

load_dotenv()
OWL_API_KEY: str | None = os.getenv('OWL_API_KEY')
OWL_INSTANCE: str | None = os.getenv('OWL_INSTANCE')
# ~2 minutes of samples at ~1 poll/sec; TTL matches so stale keys drop off with the window.
REDIS_KEY_TTL_SEC: int = 60 * 2
REDIS_MAX_SAMPLES: int = REDIS_KEY_TTL_SEC

class BackgroundTasksSerial:
    """Background tasks for the server, using a serial bus"""
    def __init__(self, manager: ConnectionManager, redis_client: redis.Redis, ser: serial.Serial) -> None:
        self.manager: ConnectionManager = manager
        self.redis_client: redis.Redis = redis_client
        self.ser: serial.Serial = ser
        self.ignore: set[str] = {'Car_ID', 'ABP', 'Time', 'BMS Disch Enable', 'InlineAcc', 'LateralAcc', 'VerticalAcc', 'RollRate', 'PitchRate', 'YawRate', 'timestamp', 'device_id'}

    def serial_parse_the_response(self, data: list[bytes]):
        """Builds a dictionary out of a list of bytes"""
        tokens: list[list[str]] = [line.decode(encoding="ascii").strip().split('=') for line in data]
        record: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "device_id": tokens[0][-1],
        }

        for token in tokens:
            key, value = token[0], token[-1]

            if key in self.ignore: continue
            if key == value: break

            record[key.lower().replace(' ', '_')] = int(value, 16)

        println(f"[{__name__}]{datetime.now().isoformat()} --- Parsed through {len(record.keys())} data points from serial bus")

        return [record]
        

    def backup_data_to_redis(self, data: list[dict[str, Any]] | None):
        """Backs up the data to Redis"""
        if not data or self.redis_client is None:
            println("No data to backup...")
            return None

        pipe = self.redis_client.pipeline()

        for record in data:
            timestamp = record.get('timestamp')
            device_id = record.get('device_id')
            for metric, value in record.items():
                if metric in self.ignore: continue

                payload = {
                    "timestamp": timestamp,
                    "value": value,
                    }

                key = f"{device_id}:{metric}"
                pipe.lpush(key, json.dumps(payload))
                # Keep lists bounded to prevent unbounded growth between expirations.
                pipe.ltrim(key, 0, REDIS_MAX_SAMPLES - 1)
                pipe.expire(key, REDIS_KEY_TTL_SEC)
        
        pipe.execute()
        println(f"[{__name__}] {datetime.now().isoformat()} --- Backed up to redis cache")

    async def serial_main(self):
        while True:
            try:
                if self.ser.in_waiting > 0:
                    println(f"[{__name__}] Attempt to read")
                    response: list[bytes] = await asyncio.to_thread(self.ser.readlines)
                    println(f"{datetime.now().isoformat()} --- Read {len(response)} lines from serial bus")

                    # Parse the data
                    println(f"[{__name__}] Attempt to parse")
                    parsed_response = self.serial_parse_the_response(response)

                    # Backup the data
                    println(f"[{__name__}] Attempt to back up")
                    _ = self.backup_data_to_redis(parsed_response)

                    # Broadcast the data
                    println(f"[{__name__}] Attempt to send up")
                    if parsed_response:
                        await self.manager.broadcast_json({"type": "data", "records": parsed_response})
                        println(f"[{__name__}] Sent")

            except Exception as e:
                println(f"[{__name__}] Error: {e}")


class BackgroundTasks:
    """Background tasks for the server"""
    def __init__(self, manager: ConnectionManager, redis_client: redis.Redis) -> None:
        self.manager: ConnectionManager = manager
        self.redis_client: redis.Redis = redis_client


    async def poll_the_dms(self, start_date: int):
        url = f"http://{OWL_INSTANCE}/public_api/Data"
        headers = { 
            "accept": "application/json", 
            "X-API-Key": OWL_API_KEY
            }
        params = {
            "startDate": start_date
            }

        async with httpx.AsyncClient() as client:
            response = await client.get(url=url, headers=headers, params=params)
            _ = response.raise_for_status()
            data = response.json()

            if not data: raise Exception("No ducks available")

            return data


    def parse_the_response(self, data: list[dict[str, Any]] | None):
        """Parses the data into a list of records"""
        if not data:
            println("No data to parse...")
            return None

        parsed = []

        for message in data:
            payload = message.get('payload', {})
            metrics = payload.get('Payload', {})
            record = {
                "timestamp": message.get('timestamp'),
                "device_id": payload.get('DeviceID')
                }
            for key, value in metrics.items():
                record[key.lower().replace(' ', '_')] = value
            parsed.append(record)

        return parsed


    def backup_data_to_redis(self, data: list[dict[str, Any]] | None):
        """Backs up the data to Redis"""
        if not data or self.redis_client is None:
            println("No data to backup...")
            return None

        pipe = self.redis_client.pipeline()

        for record in data:
            timestamp = record.get('timestamp')
            device_id = record.get('device_id')
            for metric, value in record.items():
                if metric in ("timestamp", "device_id"):
                    continue
                payload = {
                    "timestamp": timestamp,
                    "value": value,
                    }
                key = f"{device_id}:{metric}"
                pipe.lpush(key, json.dumps(payload))
                pipe.ltrim(key, 0, REDIS_MAX_SAMPLES - 1)
                pipe.expire(key, REDIS_KEY_TTL_SEC)
        
        pipe.execute()
        

    async def main(self):
        while True:
            try:
                start_date: int = int((datetime.now() - timedelta(seconds=1)).timestamp())

                # Poll the data
                response = await self.poll_the_dms(start_date)

                # Parse the data
                parsed_response = self.parse_the_response(response)

                # Backup the data
                _ = self.backup_data_to_redis(parsed_response)

                # Broadcast the data
                if parsed_response:
                    await self.manager.broadcast_json({"type": "data", "records": parsed_response})

            except asyncio.CancelledError:
                raise
            except Exception as e:
                println(f"Error: {e}")
            await asyncio.sleep(1)
            
