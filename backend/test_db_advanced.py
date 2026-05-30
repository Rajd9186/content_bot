
import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings

async def test_db_concurrency():
    print("--- Testing DB Concurrency and Transactions ---")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    workspace_id = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    async with async_session() as session:
        # 1. Test basic insert
        job_id = str(uuid.uuid4())
        await session.execute(text(
            "INSERT INTO workflow_jobs (id, workspace_id, correlation_id, created_by, status, version, created_at, updated_at) "
            "VALUES (:id, :ws, :corr, :user, 'DRAFT', 1, now(), now())"
        ), {"id": job_id, "ws": workspace_id, "corr": correlation_id, "user": user_id})
        await session.commit()
        print(f"[OK] Inserted job {job_id}")

        # 2. Test Optimistic Locking (Concurrent updates)
        async def update_job(expected_version, new_status):
            async with async_session() as s:
                result = await s.execute(text(
                    "UPDATE workflow_jobs SET status = :status, version = version + 1 "
                    "WHERE id = :id AND version = :v RETURNING version"
                ), {"status": new_status, "id": job_id, "v": expected_version})
                await s.commit()
                return result.scalar()

        print("Running concurrent updates (optimistic locking test)...")
        results = await asyncio.gather(
            update_job(1, "RUNNING"),
            update_job(1, "FAILED"),
            return_exceptions=True
        )
        
        successes = [r for r in results if r is not None and not isinstance(r, Exception)]
        print(f"Update results: {results}")
        if len(successes) == 1:
            print("[OK] Optimistic locking prevented double update.")
        else:
            print("[FAIL] Optimistic locking failed or both updates succeeded/failed incorrectly.")

        # 3. Test Foreign Key Cascade
        step_id = str(uuid.uuid4())
        await session.execute(text(
            "INSERT INTO workflow_steps (id, job_id, step_type, status, created_at) "
            "VALUES (:id, :jid, 'test_step', 'pending', now())"
        ), {"id": step_id, "jid": job_id})
        await session.commit()
        
        await session.execute(text("DELETE FROM workflow_jobs WHERE id = :id"), {"id": job_id})
        await session.commit()
        
        res = await session.execute(text("SELECT count(*) FROM workflow_steps WHERE id = :id"), {"id": step_id})
        count = res.scalar()
        if count == 0:
            print("[OK] Foreign key cascade delete works.")
        else:
            print("[FAIL] Foreign key cascade delete FAILED.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_db_concurrency())
