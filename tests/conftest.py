import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.exam import Exam

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

AGENT_KEY = "agent-key-change-in-prod"
ADMIN_KEY = "admin-key-change-in-prod"


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded_exams(db):
    exams = [
        Exam(code="EXM-T001", name="Exam Test Alpha", category="HEMATOLOGY", active=True),
        Exam(code="EXM-T002", name="Exam Test Beta", category="BIOCHEMISTRY", active=True),
        Exam(code="EXM-T003", name="Exam Test Gamma", category="ENDOCRINOLOGY", active=True),
        Exam(code="EXM-T004", name="Exam Inactive", category="HEMATOLOGY", active=False),
    ]
    db.add_all(exams)
    db.commit()
    return exams


@pytest.fixture()
def agent_headers():
    return {"X-API-Key": AGENT_KEY}


@pytest.fixture()
def admin_headers():
    return {"X-API-Key": ADMIN_KEY}
