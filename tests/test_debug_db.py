
from backend.database import SystemBase
from sqlalchemy import inspect
import backend.models

def test_tables_exist(system_engine):
    inspector = inspect(system_engine)
    tables = inspector.get_table_names()
    print(f"DEBUG TEST: Tables in system_engine: {tables}")
    assert "users" in tables
