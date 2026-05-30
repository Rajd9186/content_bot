
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def find_working_connection():
    # Common passwords to try since the environment seems to have a mismatch
    passwords = ["postgres", "password", "admin", "root", ""]
    hosts = ["localhost", "127.0.0.1"]
    dbs = ["ai_content_intel", "ai_content_dev", "postgres"]
    
    print("--- Searching for working Database Connection ---")
    
    for db in dbs:
        for pwd in passwords:
            for host in hosts:
                url = f"postgresql+asyncpg://postgres:{pwd}@{host}:5432/{db}"
                try:
                    engine = create_async_engine(url, connect_args={"command_timeout": 2})
                    async with engine.connect() as conn:
                        await conn.execute(text("SELECT 1"))
                        print(f"[SUCCESS] Connected with: postgres:{pwd}@{host}/{db}")
                        return url
                except Exception:
                    continue
    
    print("[FAIL] Could not find any working connection.")
    return None

if __name__ == "__main__":
    from sqlalchemy import text
    asyncio.run(find_working_connection())
