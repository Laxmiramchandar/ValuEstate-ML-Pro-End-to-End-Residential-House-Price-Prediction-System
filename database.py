"""
SQLite Database Layer for House Price Prediction System
Manages connection pooling, schema migrations, prediction audits, deterministic sorting,
and duplicate submission prevention.
"""
import sqlite3
import json
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config.config import Config
from config.logging_config import setup_logger

logger = setup_logger("database")

def get_db_path() -> Path:
    db_path = Path(Config.DATABASE_PATH)
    if str(Config.DATABASE_PATH) != ":memory:":
        db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path

def get_connection() -> sqlite3.Connection:
    """Creates a configured sqlite3 connection with Row factory."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables: predictions, model_versions, and application_events."""
    logger.info("Initializing SQLite database tables...")
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Predictions Audit Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_area REAL NOT NULL,
                bedrooms INTEGER NOT NULL,
                bathrooms INTEGER NOT NULL,
                age REAL NOT NULL,
                location TEXT NOT NULL,
                property_type TEXT NOT NULL,
                predicted_price REAL NOT NULL,
                formatted_price TEXT NOT NULL,
                model_version TEXT NOT NULL,
                input_payload_json TEXT NOT NULL,
                conformal_lower_bound REAL DEFAULT 0,
                conformal_upper_bound REAL DEFAULT 0,
                payload_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Schema migration check: ensure new columns exist in pre-existing tables
        cursor.execute("PRAGMA table_info(predictions)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if "conformal_lower_bound" not in existing_cols:
            cursor.execute("ALTER TABLE predictions ADD COLUMN conformal_lower_bound REAL DEFAULT 0")
        if "conformal_upper_bound" not in existing_cols:
            cursor.execute("ALTER TABLE predictions ADD COLUMN conformal_upper_bound REAL DEFAULT 0")
        if "payload_hash" not in existing_cols:
            cursor.execute("ALTER TABLE predictions ADD COLUMN payload_hash TEXT")
        
        # Index on timestamp & id for deterministic queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_created 
            ON predictions(created_at DESC, id DESC)
        """)
        
        # Model Versions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT UNIQUE NOT NULL,
                model_name TEXT NOT NULL,
                test_r2 REAL NOT NULL,
                test_rmse REAL NOT NULL,
                test_mae REAL NOT NULL,
                test_mape REAL NOT NULL,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # Application Events Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS application_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
    logger.info("Database schema initialized successfully.")

def compute_payload_hash(payload: Dict[str, Any]) -> str:
    """Computes SHA-256 hash of normalized property input payload."""
    serialized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

def insert_prediction(
    area: float,
    bedrooms: int,
    bathrooms: int,
    age: float,
    location: str,
    property_type: str,
    predicted_price: float,
    formatted_price: str,
    model_version: str,
    input_payload: Dict[str, Any],
    conformal_lower: float = 0.0,
    conformal_upper: float = 0.0,
    prevent_recent_duplicate_seconds: int = 3
) -> int:
    """
    Inserts a completed property prediction into audit table.
    Enforces duplicate prevention within recent time window.
    """
    p_hash = compute_payload_hash(input_payload)
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Duplicate submission safeguard
        if prevent_recent_duplicate_seconds > 0:
            cursor.execute("""
                SELECT id FROM predictions
                WHERE payload_hash = ? AND datetime(created_at) >= datetime('now', ?)
                ORDER BY id DESC LIMIT 1
            """, (p_hash, f"-{prevent_recent_duplicate_seconds} seconds"))
            recent = cursor.fetchone()
            if recent:
                logger.info(f"Duplicate submission prevented. Returning existing prediction ID #{recent['id']}")
                return recent["id"]
        
        cursor.execute("""
            INSERT INTO predictions (
                property_area, bedrooms, bathrooms, age, location,
                property_type, predicted_price, formatted_price,
                model_version, input_payload_json, conformal_lower_bound,
                conformal_upper_bound, payload_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            area, bedrooms, bathrooms, age, location, property_type,
            predicted_price, formatted_price, model_version,
            json.dumps(input_payload), conformal_lower, conformal_upper, p_hash
        ))
        conn.commit()
        return cursor.lastrowid

def get_recent_predictions(limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """Retrieves recent predictions using deterministic sorting: created_at DESC, id DESC."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM predictions
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_prediction_count() -> int:
    """Returns the total number of predictions logged."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM predictions")
        return cursor.fetchone()[0]

def get_prediction_by_id(prediction_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a single prediction by primary key."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM predictions WHERE id = ?", (prediction_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def record_model_version(
    version: str,
    model_name: str,
    test_r2: float,
    test_rmse: float,
    test_mae: float,
    test_mape: float,
    is_active: bool = True
):
    """Inserts or updates a model version record."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if is_active:
            cursor.execute("UPDATE model_versions SET is_active = 0")
        cursor.execute("""
            INSERT INTO model_versions (
                version, model_name, test_r2, test_rmse, test_mae, test_mape, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(version) DO UPDATE SET
                model_name = excluded.model_name,
                test_r2 = excluded.test_r2,
                test_rmse = excluded.test_rmse,
                test_mae = excluded.test_mae,
                test_mape = excluded.test_mape,
                is_active = excluded.is_active
        """, (version, model_name, test_r2, test_rmse, test_mae, test_mape, 1 if is_active else 0))
        conn.commit()
