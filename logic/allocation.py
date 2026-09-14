"""Master roll to slitter allocation rules."""


def allocate_master_rolls(required_master_rolls: int, selected_slitters: list[str]) -> dict[str, int]:
    """Evenly distribute master rolls across selected slitters.

    The first machines in the selected order receive the remainder.
    """
    if required_master_rolls <= 0:
        raise ValueError("Required Master Rolls must be greater than 0.")
    if not selected_slitters:
        raise ValueError("At least one slitter must be selected.")

    base = required_master_rolls // len(selected_slitters)
    remainder = required_master_rolls % len(selected_slitters)

    return {
        slitter: base + (1 if index < remainder else 0)
        for index, slitter in enumerate(selected_slitters)
    }


def expand_allocation(allocation: dict[str, int]) -> list[str]:
    """Expand an allocation into the per-master-roll slitter assignment order."""
    assignments: list[str] = []
    for slitter, count in allocation.items():
        if count < 0:
            raise ValueError("Machine allocation cannot be negative.")
        assignments.extend([slitter] * count)
    return assignments


def validate_allocation(required_master_rolls: int, allocation: dict[str, int]) -> list[str]:
    errors: list[str] = []
    allocated = sum(allocation.values())
    if allocated != required_master_rolls:
        difference = allocated - required_master_rolls
        errors.append(
            "Allocation Error: "
            f"Required Master Rolls: {required_master_rolls}; "
            f"Allocated Master Rolls: {allocated}; Difference: {difference}."
        )
    if any(value < 0 for value in allocation.values()):
        errors.append("Allocation Error: allocations cannot be negative.")
    return errors
