
import asyncio
import sys
import os
from sqlalchemy import text

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

async def test_db_readiness():
    try:
        # Import inside to ensure path is set
        from app.infrastructure.database import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            print("DB_STATUS: READY")
    except Exception as e:
        print(f"DB_STATUS: ERROR - {e}")

if __name__ == "__main__":
    asyncio.run(test_db_readiness())
