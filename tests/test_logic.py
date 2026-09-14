import unittest
from datetime import date

from logic.allocation import allocate_master_rolls
from logic.barcode import generate_lot_id, generate_sr_barcode
from logic.batch import generate_batch
from logic.production import calculate_production_plan
from logic.validation import parse_master_roll


class SlittingLogicTests(unittest.TestCase):
    def test_production_plan_uses_ceiling(self):
        plan = calculate_production_plan(100, 85, 10)
        self.assertEqual(plan.required_production_qty, 118)
        self.assertEqual(plan.required_master_rolls, 12)
        self.assertEqual(plan.planned_small_rolls, 120)
        self.assertEqual(plan.expected_good_rolls, 102)

    def test_allocation_distributes_remainder_to_first_machines(self):
        self.assertEqual(
            allocate_master_rolls(13, ["FX1", "FX2", "FX3"]),
            {"FX1": 5, "FX2": 4, "FX3": 4},
        )

    def test_sample_barcode_and_lot_formatter(self):
        master_roll = parse_master_roll("ULE3U1B260824UA011")
        self.assertEqual(
            generate_sr_barcode(date(2026, 8, 25), "UB", 103),
            "S260825UB3-00103",
        )
        self.assertEqual(
            generate_lot_id(
                coating_machine_code=master_roll.coating_machine_code,
                coating_date_code=master_roll.coating_date_code,
                coating_team_code=master_roll.coating_team_code,
                coating_sequence=master_roll.coating_sequence,
                slitter_machine_code="X01",
                slitting_date_code="BV25",
                slitting_team_code="V",
                slitting_sequence=103,
                slitting_position=3,
            ),
            "02BV24U011X01BV25V0010303",
        )

    def test_batch_sequence_continues_and_position_resets(self):
        master_rolls = [
            parse_master_roll("ULE3U1B260824UA011"),
            parse_master_roll("ULE3U1B260824UA012"),
        ]
        rows = generate_batch(
            product_width_mm=1000,
            parsed_master_rolls=master_rolls,
            allocation={"FX1": 1, "FX2": 1},
            actual_qty_by_master_roll={
                "ULE3U1B260824UA011": 3,
                "ULE3U1B260824UA012": 2,
            },
            slitting_date=date(2026, 8, 25),
            slitting_team="UB",
            starting_sequence=103,
        )
        self.assertEqual([row["Slitting Sequence"] for row in rows], ["00103", "00104", "00105", "00106", "00107"])
        self.assertEqual([row["Slitting Position"] for row in rows], ["01", "02", "03", "01", "02"])
        self.assertEqual(rows[0]["Product Width mm"], 1000)


if __name__ == "__main__":
    unittest.main()
