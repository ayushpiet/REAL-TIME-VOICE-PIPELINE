import asyncio
import time
import uuid
import sys
import os

# Ensure we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text, select, func
from app.db.connection import db_manager
from app.db.models import Client, DbSession, ConversationSummary
from app.repositories.client_repository import ClientRepository
from app.repositories.session_repository import SessionRepository
from app.session.manager import SessionManager

async def validate_1_returning_caller(test_phone: str):
    print("--- VALIDATION 1: Returning Caller ---")
    start = time.perf_counter()
    async with db_manager.get_session() as db:
        # First call creates client
        client1 = await ClientRepository.get_or_create_client(db, test_phone)
        client1_id = client1.id
        client1_phone = client1.phone_number
        
        # Second call returns same client
        client2 = await ClientRepository.get_or_create_client(db, test_phone)
        
        assert client1_id == client2.id, "Client UUID changed!"
        assert client1_phone == client2.phone_number, "Phone number changed!"
        
        # Check no duplicate exists
        stmt = select(func.count()).select_from(Client).where(Client.phone_number == test_phone)
        count = (await db.execute(stmt)).scalar()
        assert count == 1, f"Expected 1 client, found {count}"
        
        print("✅ Validation 1 Passed")
        print(f"Latency: {time.perf_counter() - start:.4f}s\n")
        return client1_id

async def validate_2_session_creation(client_id: uuid.UUID):
    print("--- VALIDATION 2: Session Creation ---")
    start = time.perf_counter()
    session_uuid = str(uuid.uuid4())
    async with db_manager.get_session() as db:
        db_session = await SessionRepository.create_session(db, session_uuid, client_id)
        
        assert db_session.session_id == session_uuid, "Session ID mismatch"
        assert db_session.client_id == client_id, "Client ID mismatch"
        assert db_session.started_at is not None, "started_at is None"
        assert db_session.status == "ACTIVE", "status is not ACTIVE"
        
        print("✅ Validation 2 Passed")
        print(f"Latency: {time.perf_counter() - start:.4f}s\n")
        return session_uuid

async def validate_3_session_closure(session_uuid: str):
    print("--- VALIDATION 3: Session Closure ---")
    start = time.perf_counter()
    async with db_manager.get_session() as db:
        duration = 120
        closed_session = await SessionRepository.close_session(db, session_uuid, duration)
        
        assert closed_session.status == "CLOSED", "status is not CLOSED"
        assert closed_session.duration == duration, "duration mismatch"
        assert closed_session.ended_at is not None, "ended_at is None"
        
        print("✅ Validation 3 Passed")
        print(f"Latency: {time.perf_counter() - start:.4f}s\n")

async def validate_4_summary_persistence(client_id: uuid.UUID):
    print("--- VALIDATION 4: Summary Persistence ---")
    start = time.perf_counter()
    summary_text = "This is a real generated summary of the call. The caller asked about hours."
    async with db_manager.get_session() as db:
        summary_record = await SessionRepository.save_summary(db, client_id, summary_text)
        
        assert summary_record.client_id == client_id, "Client ID mismatch in summary"
        assert summary_record.summary == summary_text, "Summary text mismatch"
        assert summary_record.updated_at is not None, "updated_at is None"
        
        # Verify exactly one active summary belongs to client
        stmt = select(func.count()).select_from(ConversationSummary).where(ConversationSummary.client_id == client_id)
        count = (await db.execute(stmt)).scalar()
        assert count == 1, f"Expected 1 summary, found {count}"
        
        print("✅ Validation 4 Passed")
        print(f"Latency: {time.perf_counter() - start:.4f}s\n")
        return summary_text

async def validate_5_summary_retrieval(client_id: uuid.UUID, expected_summary: str):
    print("--- VALIDATION 5: Summary Retrieval ---")
    start = time.perf_counter()
    async with db_manager.get_session() as db:
        retrieved_summary = await SessionRepository.get_summary(db, client_id)
        assert retrieved_summary == expected_summary, "Retrieved summary does not match expected"
        
        # Verify SessionManager metadata attachment
        sm = SessionManager()
        session_id = str(uuid.uuid4())
        sess = sm.create_session(metadata={
            "client_id": str(client_id),
            "previous_summary": retrieved_summary
        })
        
        assert sess.metadata.get("previous_summary") == retrieved_summary, "Session metadata missing summary"
        
        print("✅ Validation 5 Passed")
        print(f"Latency: {time.perf_counter() - start:.4f}s\n")

async def validate_7_concurrent_calls():
    print("--- VALIDATION 7: Concurrent Calls ---")
    start = time.perf_counter()
    
    async def simulate_call(index: int):
        phone = f"+155500000{index:02d}"
        session_id = f"test_concurrent_session_{index}"
        
        async with db_manager.get_session() as db:
            client = await ClientRepository.get_or_create_client(db, phone)
            db_session = await SessionRepository.create_session(db, session_id, client.id)
            await asyncio.sleep(0.1) # Simulate some delay
            await SessionRepository.save_summary(db, client.id, f"Summary {index}")
            await SessionRepository.close_session(db, session_id, duration=10)
            return client.id, session_id
            
    tasks = [simulate_call(i) for i in range(10)]
    results = await asyncio.gather(*tasks)
    
    client_ids = set()
    session_ids = set()
    for cid, sid in results:
        assert cid not in client_ids, "Duplicate client ID found in concurrent setup!"
        assert sid not in session_ids, "Duplicate session ID found!"
        client_ids.add(cid)
        session_ids.add(sid)
        
    print("✅ Validation 7 Passed")
    print(f"Latency for 10 concurrent calls: {time.perf_counter() - start:.4f}s\n")


async def main():
    try:
        db_manager.init_db()
        print("Database Manager Initialized.\n")
        
        test_phone = "+19998887777"
        
        client_id = await validate_1_returning_caller(test_phone)
        session_id = await validate_2_session_creation(client_id)
        await validate_3_session_closure(session_id)
        
        summary_text = await validate_4_summary_persistence(client_id)
        await validate_5_summary_retrieval(client_id, summary_text)
        
        await validate_7_concurrent_calls()
        
    finally:
        await db_manager.close()
        print("Database Connection Closed.")

if __name__ == "__main__":
    asyncio.run(main())
