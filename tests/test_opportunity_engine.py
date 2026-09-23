from fastapi.testclient import TestClient
from main import app

def test_opportunity_engine_route():
    routes = {getattr(r, "path", "") for r in app.routes}
    assert "/api/opportunity/discover" in routes

def test_query_generation():
    from app.api.opportunity import OpportunityRequest, query_set
    body = OpportunityRequest(goal="sell a clothing store", market="Tatarstan", keywords=["buyer", "wholesale"])
    queries = query_set(body)
    assert queries
    assert len(queries) <= body.max_queries
