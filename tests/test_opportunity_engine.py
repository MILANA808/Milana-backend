from fastapi.testclient import TestClient
from main import app

def test_opportunity_engine_route():
    routes = {getattr(r, "path", "") for r in app.routes}
    assert "/api/opportunity/discover" in routes

def test_universal_route_exposes_field():
    from main import app
    routes = {(getattr(r, "path", ""), getattr(r, "methods", set())) for r in app.routes}
    assert any(path == "/api/universal" and "POST" in methods for path, methods in routes)

def test_query_generation():
    from app.api.opportunity import OpportunityRequest, query_set
    body = OpportunityRequest(goal="sell a clothing store", market="Tatarstan", keywords=["buyer", "wholesale"])
    queries = query_set(body)
    assert queries
    assert len(queries) <= body.max_queries
