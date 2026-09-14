"""Validation and parsing for operator-entered manufacturing data."""

from dataclasses import dataclass
import re

from data.config import VALID_COATING_MACHINES, VALID_COATING_TEAMS
from logic.barcode import convert_date_to_letter_code, parse_yymmdd


@dataclass(frozen=True)
class ParsedMasterRoll:
    sn: str
    coating_machine_original: str
    coating_machine_code: str
    coating_date_original: str
    coating_date_code: str
    coating_team_original: str
    coating_team_code: str
    coating_sequence: str


def normalize_master_roll_lines(raw_text: str) -> list[str]:
    return [line.strip().upper() for line in raw_text.splitlines() if line.strip()]


def find_duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def parse_master_roll(sn: str) -> ParsedMasterRoll:
    """Parse and validate a Master Roll SN from the upstream coating system."""
    if len(sn) != 18:
        raise ValueError(f"{sn}: MR length must be exactly 18 characters.")
    if sn[:4] != "ULE3":
        raise ValueError(f"{sn}: MR prefix must be ULE3.")

    coating_machine = sn[4:7]
    coating_date_raw = sn[7:13]
    coating_team = sn[13:15]
    coating_sequence = sn[15:18]

    if coating_machine not in VALID_COATING_MACHINES:
        raise ValueError(f"{sn}: unsupported coating machine {coating_machine}.")
    if coating_team not in VALID_COATING_TEAMS:
        raise ValueError(f"{sn}: unsupported coating team {coating_team}.")
    if not re.fullmatch(r"\d{3}", coating_sequence):
        raise ValueError(f"{sn}: coating sequence must be exactly 3 digits.")

    coating_date = parse_yymmdd(coating_date_raw)
    coating_date_code = convert_date_to_letter_code(coating_date)

    coating_machine_code = {"U1A": "01", "U1B": "02"}[coating_machine]
    coating_team_code = {"UA": "U", "UB": "V"}[coating_team]

    return ParsedMasterRoll(
        sn=sn,
        coating_machine_original=coating_machine,
        coating_machine_code=coating_machine_code,
        coating_date_original=coating_date_raw,
        coating_date_code=coating_date_code,
        coating_team_original=coating_team,
        coating_team_code=coating_team_code,
        coating_sequence=coating_sequence,
    )


def validate_master_rolls(raw_text: str, required_count: int) -> tuple[list[ParsedMasterRoll], list[str]]:
    sns = normalize_master_roll_lines(raw_text)
    errors: list[str] = []

    if len(sns) != required_count:
        errors.append(f"Required {required_count} Master Rolls but {len(sns)} entered.")

    duplicates = find_duplicates(sns)
    if duplicates:
        errors.append(f"Duplicate Master Roll detected: {', '.join(duplicates)}.")

    parsed: list[ParsedMasterRoll] = []
    for sn in sns:
        try:
            parsed.append(parse_master_roll(sn))
        except ValueError as exc:
            errors.append(str(exc))

    return parsed, errors


def validate_generated_batch(rows: list[dict[str, str | int]]) -> list[str]:
    errors: list[str] = []
    sr_barcodes = [str(row["SR Barcode"]) for row in rows]
    lot_ids = [str(row["LOT ID"]) for row in rows]

    duplicate_sr = find_duplicates(sr_barcodes)
    if duplicate_sr:
        errors.append(f"Duplicate SR barcode detected: {', '.join(duplicate_sr)}.")

    duplicate_lot = find_duplicates(lot_ids)
    if duplicate_lot:
        errors.append(f"Duplicate LOT ID detected: {', '.join(duplicate_lot)}.")

    for row in rows:
        if len(str(row["LOT ID"])) != 25:
            errors.append(f"LOT ID length error for {row['LOT ID']}.")

    sequences = [int(row["Slitting Sequence"]) for row in rows]
    if sequences and sequences != list(range(sequences[0], sequences[0] + len(sequences))):
        errors.append("Slitting sequence must be continuous.")

    positions_by_mr: dict[str, list[int]] = {}
    for row in rows:
        positions_by_mr.setdefault(str(row["Master Roll SN"]), []).append(int(row["Slitting Position"]))
    for mr_sn, positions in positions_by_mr.items():
        expected = list(range(1, len(positions) + 1))
        if positions != expected:
            errors.append(f"Position must reset to 01 for Master Roll {mr_sn}.")

    return errors
