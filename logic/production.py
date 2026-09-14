"""Production planning calculations."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ProductionPlan:
    shipment_qty: int
    yield_percent: float
    planning_small_rolls_per_cut: int
    required_production_qty: int
    required_master_rolls: int
    planned_small_rolls: int
    expected_good_rolls: int


def calculate_production_plan(
    shipment_qty: int,
    yield_percent: float,
    planning_small_rolls_per_cut: int,
) -> ProductionPlan:
    """Calculate the required production plan using ceiling, never rounding."""
    if shipment_qty <= 0:
        raise ValueError("Shipment Qty must be greater than 0.")
    if yield_percent <= 0 or yield_percent > 100:
        raise ValueError("Target Yield % must be greater than 0 and less than or equal to 100.")
    if planning_small_rolls_per_cut <= 0:
        raise ValueError("Planning Small Rolls per Cut must be greater than 0.")

    required_production_qty = math.ceil(shipment_qty / (yield_percent / 100))
    required_master_rolls = math.ceil(required_production_qty / planning_small_rolls_per_cut)
    planned_small_rolls = required_master_rolls * planning_small_rolls_per_cut
    expected_good_rolls = math.ceil(planned_small_rolls * yield_percent / 100)

    return ProductionPlan(
        shipment_qty=shipment_qty,
        yield_percent=yield_percent,
        planning_small_rolls_per_cut=planning_small_rolls_per_cut,
        required_production_qty=required_production_qty,
        required_master_rolls=required_master_rolls,
        planned_small_rolls=planned_small_rolls,
        expected_good_rolls=expected_good_rolls,
    )
