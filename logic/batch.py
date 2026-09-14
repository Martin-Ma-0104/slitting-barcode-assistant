"""Batch generation from validated input records."""

from datetime import date

from logic.allocation import expand_allocation
from logic.barcode import (
    convert_date_to_letter_code,
    convert_slitter_machine,
    convert_team,
    generate_lot_id,
    generate_sr_barcode,
)
from logic.validation import ParsedMasterRoll


def generate_batch(
    product_width_mm: float,
    parsed_master_rolls: list[ParsedMasterRoll],
    allocation: dict[str, int],
    actual_qty_by_master_roll: dict[str, int],
    slitting_date: date,
    slitting_team: str,
    starting_sequence: int,
) -> list[dict[str, str | int]]:
    assignments = expand_allocation(allocation)
    if len(assignments) != len(parsed_master_rolls):
        raise ValueError("Machine allocation count must match Master Roll count.")
    if product_width_mm <= 0:
        raise ValueError("Product Width must be greater than 0.")

    slitting_date_code = convert_date_to_letter_code(slitting_date)
    slitting_team_code = convert_team(slitting_team)

    rows: list[dict[str, str | int]] = []
    current_sequence = starting_sequence

    for master_roll, slitter in zip(parsed_master_rolls, assignments):
        actual_qty = int(actual_qty_by_master_roll[master_roll.sn])
        if actual_qty <= 0:
            raise ValueError(f"Actual Small Roll Qty must be > 0 for {master_roll.sn}.")

        slitter_machine_code = convert_slitter_machine(slitter)

        # Business rule: position resets for each Master Roll, sequence does not.
        for position in range(1, actual_qty + 1):
            sr_barcode = generate_sr_barcode(slitting_date, slitting_team, current_sequence)
            lot_id = generate_lot_id(
                coating_machine_code=master_roll.coating_machine_code,
                coating_date_code=master_roll.coating_date_code,
                coating_team_code=master_roll.coating_team_code,
                coating_sequence=master_roll.coating_sequence,
                slitter_machine_code=slitter_machine_code,
                slitting_date_code=slitting_date_code,
                slitting_team_code=slitting_team_code,
                slitting_sequence=current_sequence,
                slitting_position=position,
            )

            rows.append(
                {
                    "Product Width mm": product_width_mm,
                    "Master Roll SN": master_roll.sn,
                    "Assigned Slitter": slitter,
                    "SR Barcode": sr_barcode,
                    "Coating Machine Original": master_roll.coating_machine_original,
                    "Coating Machine Code": master_roll.coating_machine_code,
                    "Coating Date Original": master_roll.coating_date_original,
                    "Coating Date Code": master_roll.coating_date_code,
                    "Coating Team Original": master_roll.coating_team_original,
                    "Coating Team Code": master_roll.coating_team_code,
                    "Coating Sequence": master_roll.coating_sequence,
                    "Slitting Date": slitting_date.strftime("%Y-%m-%d"),
                    "Slitting Date Code": slitting_date_code,
                    "Slitting Team Original": slitting_team,
                    "Slitting Team Code": slitting_team_code,
                    "Slitting Sequence": f"{current_sequence:05d}",
                    "Slitting Position": f"{position:02d}",
                    "Slitter Machine Code": slitter_machine_code,
                    "LOT ID": lot_id,
                }
            )
            current_sequence += 1

    return rows
