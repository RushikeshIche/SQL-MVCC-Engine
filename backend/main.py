from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import sys
import os

# Add the engine to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from engine.database import Database

app = FastAPI(title="SQL MVCC Engine API", version="1.0.0")

# FIXED CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Global database instance
db = Database("mvcc_database")

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    transaction_id: Optional[int] = None

class TransactionRequest(BaseModel):
    isolation_level: str = "READ_COMMITTED"

class QueryResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]] = []
    columns: List[str] = []
    message: str = ""
    execution_time: float = 0.0
    affected_rows: int = 0
    transaction_id: Optional[int] = None
    error: Optional[str] = None

class TransactionResponse(BaseModel):
    transaction_id: int
    status: str
    message: str

class TableInfo(BaseModel):
    name: str
    columns: List[str]
    record_count: int
    created_at: str

@app.get("/")
async def root():
    return {"message": "SQL MVCC Engine API"}

@app.post("/execute", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Execute SQL query"""
    import time
    start_time = time.time()
    
    try:
        print(f"📨 Received query: {request.query}")
        result = db.execute(request.query, request.transaction_id)
        execution_time = time.time() - start_time
        print(f"✅ Query executed in {execution_time:.3f}s")
        
        return QueryResponse(
            success=result['success'],
            data=result.get('data', []),
            columns=result.get('columns', []),
            message=result.get('message', ''),
            execution_time=execution_time,
            affected_rows=result.get('affected_rows', 0),
            transaction_id=result.get('txn_id')
        )
    except Exception as e:
        error_time = time.time() - start_time
        print(f"❌ Query failed: {str(e)}")
        return QueryResponse(
            success=False,
            error=str(e),
            execution_time=error_time
        )

@app.post("/transaction/begin", response_model=TransactionResponse)
async def begin_transaction(request: TransactionRequest):
    """Start a new transaction"""
    try:
        txn_id = db.begin_transaction(request.isolation_level)
        print(f"🔄 Transaction {txn_id} started")
        return TransactionResponse(
            transaction_id=txn_id,
            status="ACTIVE",
            message=f"Transaction {txn_id} started"
        )
    except Exception as e:
        print(f"❌ Failed to start transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transaction/{txn_id}/commit")
async def commit_transaction(txn_id: int):
    """Commit transaction"""
    try:
        success = db.commit_transaction(txn_id)
        message = f"Transaction {txn_id} committed" if success else "Commit failed"
        print(f"✅ {message}")
        return {
            "success": success,
            "message": message
        }
    except Exception as e:
        print(f"❌ Failed to commit transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transaction/{txn_id}/rollback")
async def rollback_transaction(txn_id: int):
    """Rollback transaction"""
    try:
        success = db.rollback_transaction(txn_id)
        message = f"Transaction {txn_id} rolled back" if success else "Rollback failed"
        print(f"🔄 {message}")
        return {
            "success": success,
            "message": message
        }
    except Exception as e:
        print(f"❌ Failed to rollback transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tables")
async def get_tables():
    """Get all tables"""
    try:
        tables = []
        for table_name in db.storage.get_table_names():
            table_info = db.storage.tables[table_name]
            tables.append(TableInfo(
                name=table_name,
                columns=table_info['columns'],
                record_count=len(table_info['records']),
                created_at=table_info['created_at']
            ))
        print(f"📊 Returning {len(tables)} tables")
        return tables
    except Exception as e:
        print(f"❌ Failed to get tables: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": "connected"}

if __name__ == "__main__":
    import uvicorn
    print(" Starting SQL MVCC Engine API...")
    print(" Backend URL: http://localhost:8000")
    print(" API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")