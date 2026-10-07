import io
import os
import shutil
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base, get_db
from app.config.settings import settings
from app.main import app
from app.rag.vector_store import VectorStore

# Temporary test directory
TEST_DIR = Path(tempfile.mkdtemp(prefix="multimind_test_"))
TEST_DB_URL = f"sqlite:///{TEST_DIR}/test.db"

test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    # Configure settings for test run
    settings.VECTOR_DB_PATH = str(TEST_DIR / "vector_store")
    settings.UPLOAD_DIR = TEST_DIR / "uploads"
    settings.PROCESSED_DIR = TEST_DIR / "processed"
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    Path(settings.VECTOR_DB_PATH).mkdir(parents=True, exist_ok=True)

    Base.metadata.create_all(bind=test_engine)
    yield
    # Cleanup
    shutil.rmtree(TEST_DIR, ignore_errors=True)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture
def test_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_csv_bytes() -> bytes:
    content = "date,product,category,revenue,cost\n2025-01-01,Alpha,Electronics,1000,600\n2025-01-02,Beta,Furniture,1500,900\n2025-01-03,Alpha,Electronics,1200,700\n2025-01-04,Gamma,Software,2000,1000\n2025-01-05,Beta,Furniture,1800,1100\n"
    return content.encode("utf-8")

@pytest.fixture
def sample_txt_bytes() -> bytes:
    content = "Artificial Intelligence and Machine Learning.\nSupervised learning uses labeled training data to learn mapping functions.\nUnsupervised learning identifies hidden clusters and distributions.\nReinforcement learning trains agents using reward feedback signals."
    return content.encode("utf-8")
