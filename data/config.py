"""Shared manufacturing constants for the V1 slitting barcode app."""

SLITTER_MACHINE_CODES: dict[str, str] = {
    "FX1": "X01",
    "FX2": "X02",
    "FX3": "X03",
    "FX4": "X04",
    "FX5": "X05",
    "FX6": "X06",
    "FX7": "X07",
}

COATING_MACHINE_CODES: dict[str, str] = {
    "U1A": "01",
    "U1B": "02",
}

TEAM_CODES: dict[str, str] = {
    "UA": "U",
    "UB": "V",
}

MONTH_LETTER_CODES: dict[int, str] = {
    1: "O",
    2: "P",
    3: "Q",
    4: "R",
    5: "S",
    6: "T",
    7: "U",
    8: "V",
    9: "W",
    10: "X",
    11: "Y",
    12: "Z",
}

VALID_SLITTING_TEAMS = tuple(TEAM_CODES.keys())
VALID_COATING_TEAMS = tuple(TEAM_CODES.keys())
VALID_COATING_MACHINES = tuple(COATING_MACHINE_CODES.keys())
VALID_SLITTERS = tuple(SLITTER_MACHINE_CODES.keys())

PRODUCT_LINE_CODE = "3"
MIN_LETTER_CODE_YEAR = 2025

MES_EXPORT_COLUMNS = [
    "小分切条码",
    "涂覆条码",
    "涂覆机台",
    "涂覆日期",
    "涂覆班组",
    "涂覆流水",
    "小分切工位",
    "小分切机台",
]
