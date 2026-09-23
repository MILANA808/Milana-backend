from app.science.discovery import DiscoveryEngine, Hypothesis, Experiment

def test_engine_prefers_discriminating_experiment():
    hs=[
        Hypothesis("A","y=x",lambda x:x),
        Hypothesis("B","y=x+1",lambda x:x+1),
        Hypothesis("C","y=2x",lambda x:2*x),
    ]
    exps=[
        Experiment("weak",0,cost=1),
        Experiment("strong",2,cost=1),
    ]
    engine=DiscoveryEngine(hs)
    choice=engine.choose_experiment(exps)
    assert choice["selected"]["experiment_id"]=="strong"

def test_observation_eliminates_inconsistent_hypotheses():
    hs=[
        Hypothesis("A","y=x",lambda x:x),
        Hypothesis("B","y=x+1",lambda x:x+1),
    ]
    engine=DiscoveryEngine(hs)
    obs=engine.observe(Experiment("e",3),3)
    assert obs.survivors==("A",)
    assert engine.active_ids==["A"]

def test_hash_is_reproducible():
    hs=[Hypothesis("A","zero",lambda x:0),Hypothesis("B","one",lambda x:1)]
    a=DiscoveryEngine(hs).observe(Experiment("e",7),0)
    b=DiscoveryEngine(hs).observe(Experiment("e",7),0)
    assert a.observation_hash==b.observation_hash
