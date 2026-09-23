import os
os.environ["AKSI_TASK_DB"]="/tmp/aksi-sampling-test.sqlite3"
from app.semantic_sampling import SemanticSampler, reconstruction_metrics, semantic_delta, semantic_state, reconstruct_from_checkpoints

def base(): return {"status":"CREATED","plan":[],"journal":[],"sources":[],"findings":[],"analysis":"","verification":{},"report":None,"receipt":None}

def test_adaptive_sampler_keeps_semantic_transitions():
    sampler=SemanticSampler(threshold=0.2,max_gap=4); runtime=base()
    for i in range(20):
        runtime["journal"].append({"message":"noise","status":"running"})
        if i==8: runtime["sources"].append({"url":"https://example.com/a"})
        if i==14: runtime["analysis"]="ready"
        sampler.observe(runtime,"обычное наблюдение","running")
    s=runtime["sampling"]; assert len(s["checkpoints"])<s["events_total"]; assert any(c["reason"]=="semantic_delta" for c in s["checkpoints"])

def test_reconstruction_marks_unobserved_events_unknown():
    sampler=SemanticSampler(threshold=0.99,max_gap=100); runtime=base()
    for _ in range(5): sampler.observe(runtime,"noise","running")
    recon=reconstruct_from_checkpoints(runtime["sampling"]["checkpoints"],5)
    assert recon[0]["known"] is True and all(not x["known"] for x in recon[1:])

def test_reconstruction_metrics_have_zero_error_at_checkpoints():
    sampler=SemanticSampler(threshold=0.2,max_gap=2); runtime=base(); full=[]
    for i in range(10):
        if i==5: runtime["status"]="ANALYZING"
        full.append(dict(semantic_state(runtime))); sampler.observe(runtime,"обычное наблюдение","running")
    m=reconstruction_metrics(full,runtime["sampling"]["checkpoints"]); assert m["events"]==10; assert m["checkpoints"]>=1; assert m["checkpoint_state_error_rate"]==0.0

def test_delta_is_bounded():
    assert 0.0<=semantic_delta({"a":1},{"a":1})<=1.0; assert 0.0<=semantic_delta({"a":1},{"a":2})<=1.0