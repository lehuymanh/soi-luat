"""bench/llm/run.py: phần chỉnh (--skip) không được lẫn câu của phần chấm."""

import importlib.util
from pathlib import Path


def _run():
    spec = importlib.util.spec_from_file_location("bench_llm_run", Path(__file__).parents[1] / "bench" / "llm" / "run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_pick_sample_holds_out_exactly_the_scored_questions():
    run = _run()
    for n in (60, 100, 150, 300):  # random.sample đổi thuật toán theo cỡ: thử qua nhiều cỡ kho
        qs = [{"id": str(i)} for i in range(n)]
        held = {q["id"] for q in run.pick_sample(qs, 15)}
        tune = [q["id"] for q in run.pick_sample(qs, 30, skip=15)]
        assert len(held) == 15 and len(tune) == 30 and held.isdisjoint(tune)
    assert run.pick_sample(qs, 5, skip=len(qs)) == []
