from app.core.cognitive_runtime import candidate_score, decompose, route, safe_math

def test_safe_math_is_restricted_and_correct():
    assert safe_math("2 + 3 * 4") == 14
    assert safe_math("__import__('os').system('x')") is None

def test_route_and_decomposition():
    rt = route("Сравни два подхода и найди исследования")
    assert rt["needs_web"] is True
    assert len(decompose("Сравни два подхода и найди исследования", rt)) == 3

def test_candidate_score_rewards_evidence_and_domains():
    evidence = [
        {"source": "A", "url": "https://a.example/x", "text": "AKSI evidence supports a mathematical controller."},
        {"source": "B", "url": "https://b.example/x", "text": "Independent evidence discusses a controller and arbitration."},
    ]
    good = candidate_score(
        "AKSI uses a mathematical controller and arbitration supported by evidence.",
        "AKSI mathematical controller",
        evidence,
        "analytical",
        ["AKSI uses a mathematical controller and arbitration supported by evidence.", "other candidate"],
    )
    assert 0 < good["total"] <= 1
    assert good["diversity"] > 0
