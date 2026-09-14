"""Deterministic barcode and LOT ID generation."""

from datetime import date, datetime

from data.config import (
    COATING_MACHINE_CODES,
    MIN_LETTER_CODE_YEAR,
    MONTH_LETTER_CODES,
    PRODUCT_LINE_CODE,
    SLITTER_MACHINE_CODES,
    TEAM_CODES,
)


def convert_date_to_letter_code(value: date) -> str:
    """Convert a calendar date to the manufacturing letter date code."""
    if value.year < MIN_LETTER_CODE_YEAR:
        raise ValueError("Date year must be 2025 or later.")

    year_offset = value.year - MIN_LETTER_CODE_YEAR
    if year_offset > 25:
        raise ValueError("Date year is outside supported A-Z letter range.")

    year_letter = chr(ord("A") + year_offset)
    month_letter = MONTH_LETTER_CODES[value.month]
    return f"{year_letter}{month_letter}{value.day:02d}"


def parse_yymmdd(raw_value: str) -> date:
    try:
        return datetime.strptime(raw_value, "%y%m%d").date()
    except ValueError as exc:
        raise ValueError(f"Invalid YYMMDD date: {raw_value}") from exc


def convert_coating_machine(machine: str) -> str:
    if machine not in COATING_MACHINE_CODES:
        raise ValueError(f"Unsupported coating machine code: {machine}")
    return COATING_MACHINE_CODES[machine]


def convert_slitter_machine(slitter: str) -> str:
    if slitter not in SLITTER_MACHINE_CODES:
        raise ValueError(f"Unsupported slitter machine: {slitter}")
    return SLITTER_MACHINE_CODES[slitter]


def convert_team(team: str) -> str:
    if team not in TEAM_CODES:
        raise ValueError(f"Unsupported team code: {team}")
    return TEAM_CODES[team]


def format_slitting_sequence(sequence: int) -> str:
    if sequence < 0 or sequence > 99999:
        raise ValueError("Slitting sequence must be between 0 and 99999.")
    return f"{sequence:05d}"


def generate_sr_barcode(slitting_date: date, slitting_team: str, slitting_sequence: int) -> str:
    convert_team(slitting_team)
    return (
        f"S{slitting_date.strftime('%y%m%d')}"
        f"{slitting_team}{PRODUCT_LINE_CODE}-"
        f"{format_slitting_sequence(slitting_sequence)}"
    )


def generate_lot_id(
    coating_machine_code: str,
    coating_date_code: str,
    coating_team_code: str,
    coating_sequence: str,
    slitter_machine_code: str,
    slitting_date_code: str,
    slitting_team_code: str,
    slitting_sequence: int,
    slitting_position: int,
) -> str:
    lot_id = (
        f"{coating_machine_code}"
        f"{coating_date_code}"
        f"{coating_team_code}"
        f"{coating_sequence}"
        f"{slitter_machine_code}"
        f"{slitting_date_code}"
        f"{slitting_team_code}"
        f"{format_slitting_sequence(slitting_sequence)}"
        f"{slitting_position:02d}"
    )
    if len(lot_id) != 25:
        raise ValueError(f"Generated LOT ID must be 25 characters, got {len(lot_id)}.")
    return lot_id
