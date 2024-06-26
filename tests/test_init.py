import cloudai  # noqa: F401
from cloudai._core.registry import Registry


def test_system_parsers():
    parsers = Registry().system_parsers_map.keys()
    assert "standalone" in parsers
    assert "slurm" in parsers
    assert len(parsers) == 2
