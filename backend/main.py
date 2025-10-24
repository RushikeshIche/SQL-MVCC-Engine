from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import sys
import os
import asyncio
import json

# Add the engine to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from engine.database import Database

app = FastAPI(title="SQL MVCC Engine API", version="1.0.0")

# FIXED CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"🔌 WebSocket client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        print(f"🔌 WebSocket client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"❌ Error sending to WebSocket: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)

# Global instances
db = Database("mvcc_database")
ws_manager = ConnectionManager()

# Register callback for transaction state changes
def on_transaction_state_change(stats):
    """Callback when transaction state changes"""
    # Schedule broadcast in the event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(ws_manager.broadcast({
                'type': 'transaction_stats',
                'data': stats
            }))
    except Exception as e:
        print(f"Error broadcasting state change: {e}")

db.mvcc.register_state_change_callback(on_transaction_state_change)

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

@app.get("/transaction/statistics")
async def get_transaction_statistics():
    """Get current transaction statistics"""
    try:
        stats = db.mvcc.get_transaction_statistics()
        print(f"📊 Returning transaction statistics")
        return stats
    except Exception as e:
        print(f"❌ Failed to get transaction statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transaction/clear-history")
async def clear_transaction_history():
    """Clear transaction history (resets visualization, not data)"""
    try:
        # Reset the MVCC transaction tracking
        db.mvcc.transactions.clear()
        db.mvcc.transaction_snapshots.clear()
        db.mvcc.transaction_stats = {
            'active': 0,
            'committed': 0,
            'aborted': 0,
            'total': 0
        }
        db.mvcc.next_txn_id = 1
        
        # Broadcast the reset to all connected clients
        empty_stats = {
            'stats': {'active': 0, 'committed': 0, 'aborted': 0, 'total': 0},
            'active_transactions': [],
            'committed_transactions': [],
            'aborted_transactions': [],
            'timestamp': datetime.now().isoformat()
        }
        await ws_manager.broadcast({
            'type': 'transaction_stats',
            'data': empty_stats
        })
        
        print("🧹 Transaction history cleared")
        return {"success": True, "message": "Transaction history cleared"}
    except Exception as e:
        print(f"❌ Failed to clear history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/transactions")
async def websocket_transactions(websocket: WebSocket):
    """WebSocket endpoint for real-time transaction updates"""
    await ws_manager.connect(websocket)
    try:
        # Send initial state
        initial_stats = db.mvcc.get_transaction_statistics()
        await websocket.send_json({
            'type': 'transaction_stats',
            'data': initial_stats
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Echo back or handle commands if needed
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        print("🔌 WebSocket client disconnected normally")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        ws_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    print(" Starting SQL MVCC Engine API...")
    print(" Backend URL: http://localhost:8000")
    print(" API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")