import pytest

from navpy import Budget, BudgetExceeded


def test_steps_within_budget():
    b = Budget(max_steps=3, max_cost_usd=1.0)
    assert b.tick() == 1
    assert b.tick() == 2
    assert b.tick() == 3
    assert b.remaining_steps() == 0


def test_step_budget_raises():
    b = Budget(max_steps=2)
    b.tick()
    b.tick()
    with pytest.raises(BudgetExceeded):
        b.tick()


def test_cost_budget_raises():
    b = Budget(max_cost_usd=0.10)
    b.add_cost(0.05)
    assert b.cost_usd == pytest.approx(0.05)
    with pytest.raises(BudgetExceeded):
        b.add_cost(0.20)


def test_negative_cost_ignored():
    b = Budget(max_cost_usd=0.10)
    b.add_cost(-5)
    assert b.cost_usd == 0.0
