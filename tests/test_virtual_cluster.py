from app.core.virtual_cluster import VirtualGPUCluster


def test_map_sum_is_verified():
    cluster = VirtualGPUCluster(workers=4, seed=7)
    result = cluster.map_sum([float(i) for i in range(1001)])
    assert result["verified"] is True
    assert result["result"] == result["reference"]
    assert result["workers"] == 4


def test_tiny_model_training_converges():
    result = VirtualGPUCluster(workers=3).train_linear_demo(samples=512, steps=250, learning_rate=0.05)
    assert result["verified_converged"] is True
    assert abs(result["learned_weight"] - 2.5) < 0.15
    assert abs(result["learned_bias"] + 0.7) < 0.15


def test_limits_are_validated():
    import pytest
    with pytest.raises(ValueError):
        VirtualGPUCluster(workers=0)
    with pytest.raises(ValueError):
        VirtualGPUCluster().train_linear_demo(samples=2)
