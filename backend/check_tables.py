import asyncio
import asyncpg

url = "postgresql://verified_ai_user:GTxRReQkeAGiMnQRWHMXE7CvMfyXMQX3@dpg-d8aa2jcm0tmc739u2e30-a.oregon-postgres.render.com/verified_ai"

async def main():
    conn = await asyncpg.connect(url, ssl="require")
    try:
        rows = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' ORDER BY table_name
        """)
        print("Tables:", [r["table_name"] for r in rows])
    finally:
        await conn.close()

asyncio.run(main())
