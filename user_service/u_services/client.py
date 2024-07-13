import os
import aiohttp
import asyncio
from flask import jsonify
from dotenv import load_dotenv
load_dotenv()

async def fetch_data(session, url,token):
    headers = {'Authorization': token}
    async with session.post(url, headers=headers, timeout=5) as response:
        response.raise_for_status()  # Check if the request was successful
        return await response.json()  # Properly await the response


async def validate_token(token):
    async with aiohttp.ClientSession() as session:
        try:
            data = await fetch_data(session, os.getenv('SHARED_SERVICES'),token)
            return data
        except aiohttp.ClientConnectionError as ce:
            return {'error': 'Connection error occurred', 'details': str(ce)}
        except aiohttp.ClientError as e:
            return {'error': 'An error occurred', 'details': str(e)}
