from app.core.aksi_field import DynamicField, run_field

def test_field_is_deterministic():
    a=run_field('Москва находится в России.', [{'url':'https://example.org'}], 0.6)
    b=run_field('Москва находится в России.', [{'url':'https://example.org'}], 0.6)
    assert a == b

def test_operator_selection_changes_with_context():
    f=DynamicField(); r1=f.step('один сигнал'); assert 'hdc' in r1['active_operators']
    r2=f.step('новый сигнал для анализа', external_evidence=2, confidence=0.2)
    assert 'uncertainty' in r2['active_operators'] and 'counterfactual' in r2['active_operators']

def test_prediction_error_and_stability_are_exposed():
    f=DynamicField(); f.step('альфа бета'); r=f.step('гамма дельта')
    assert 'prediction_error' in r and 0 <= r['stability'] <= 1

def test_counterfactuals_are_bounded():
    f=DynamicField(); f.step('state'); xs=f.counterfactual(['a','b','c','d','e','f','g','h','i'])
    assert len(xs)==8

def test_session_persists_trajectory():
    from app.core.aksi_field import run_field
    sid="test-persistent-field"
    a=run_field("alpha beta",session_id=sid)
    b=run_field("beta gamma",session_id=sid)
    assert b["session_id"] == sid
    assert b["field"]["step"] == a["field"]["step"] + 1
    assert b["field"]["memory_size"] >= a["field"]["memory_size"]

def test_benchmark_has_dynamic_and_fixed_baselines():
    from benchmarks.aksi_field_benchmark import benchmark
    result=benchmark()
    assert set(result) == {"stable","regime_switch","noisy"}
    for case in result.values():
        assert set(case) == {"dynamic","fixed"}
        assert case["dynamic"]["operator_count"] <= case["fixed"]["operator_count"]
