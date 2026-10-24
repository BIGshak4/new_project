"""Explicit-world verification of silence updates and clock/counterexample checks."""

import importlib.util
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("public_signals", BANK / "solutions/prep_113_public_signal_rounds.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def run_checks():
    worlds_checked = actor_checks = no_public_fact_worlds = 0
    for population in range(1, 10):
        events, unresolved = model.first_signal_layers(population)
        assert not unresolved
        assert len(events) == (1 << population) - 1
        for world, (round_number, actors) in events.items():
            # Independent count/identity oracle after state-elimination modeling.
            assert round_number == world.bit_count()
            assert set(actors) == {i for i in range(population) if world & (1 << i)}
            worlds_checked += 1
            actor_checks += len(actors)
        no_fact_events, no_fact_unresolved = model.first_signal_layers(population, common_exists=False)
        assert no_fact_events == {}
        assert no_fact_unresolved == set(range(1 << population))
        no_public_fact_worlds += len(no_fact_unresolved)
    assert model.elapsed_whole_hours(23, 4, days_later=1) == 5
    assert [model.elapsed_whole_hours(23, hour, days_later=1) for hour in range(5)] == [1, 2, 3, 4, 5]
    assert model.elapsed_whole_hours(23, 4, days_later=2) == 29
    cases = model.source_only_counterexamples()
    assert all(5 in value["air_signal_rounds"] for value in cases.values())
    assert cases["repeat_allowed"]["liars"] == 1
    assert cases["first_eligible_not_compulsory"]["air_signal_rounds"] == (5,)
    assert cases["edited_first_signal"]["liars"] == 5
    one_liar_events, _ = model.first_signal_layers(1)
    five_liar_events, _ = model.first_signal_layers(5)
    earliest_known_opportunity = one_liar_events[1][0]
    assert earliest_known_opportunity == 1
    for name in ("repeat_allowed", "first_eligible_not_compulsory"):
        history = cases[name]["air_signal_rounds"]
        assert all(type(round_) is int and round_ >= earliest_known_opportunity
                   for round_ in history)
    assert five_liar_events[0b11111][0] == 5
    rejected = 0
    for args in [(23, 23, 0), (24, 4, 1), (23, -1, 1)]:
        try:
            model.elapsed_whole_hours(args[0], args[1], days_later=args[2])
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(args)
    for population in (0, 13, True):
        try:
            model.first_signal_layers(population)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(population)
    return {"question_id": "PREP-113", "status": "passed", "explicit_nonempty_worlds": worlds_checked,
            "first_signal_actor_checks": actor_checks, "without_common_fact_worlds_unresolved": no_public_fact_worlds,
            "population_range": [1, 9], "source_only_counterexamples": 2,
            "next_morning_elapsed_rounds": 5, "invalid_cases_rejected": rejected,
            "scope": "Exhaustive finite epistemic worlds up to nine couples; induction handles 200. Missing source assumptions are not treated as established facts. No physical signaling experiment."}


if __name__ == "__main__":
    result = run_checks()
    (BANK / "checks/prep-113-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
