import re
from typing import Iterable, List, Tuple, Union


WELL_RE = re.compile(r"^([A-Za-z]+)\s*(\d+)$")


"""
services/well_translator.py

Helper functions for translating and validating plate well designators.
"""


def row_label_to_index(row_label: str) -> int:
    """Convert row label like 'A' or 'AA' (case-insensitive) to zero-based index."""
    if not isinstance(row_label, str) or not row_label.strip():
        raise ValueError("row_label must be a non-empty string")
    s = row_label.strip().upper()
    idx = 0
    for ch in s:
        if not ('A' <= ch <= 'Z'):
            raise ValueError(f"invalid row character: {ch!r}")
        idx = idx * 26 + (ord(ch) - ord('A') + 1)
    return idx - 1


def column_to_index(column: Union[int, str]) -> int:
    """Convert column (1-based) to zero-based index. Accepts int or numeric string."""
    try:
        c = int(column)
    except Exception as exc:
        raise ValueError("column must be an integer or string representing an integer") from exc
    if c < 1:
        raise ValueError("column must be >= 1")
    return c - 1


def well_to_indices(row: str, column: Union[int, str]) -> Tuple[int, int]:
    """Convert (row label, column) -> (row_index, col_index), both zero-based."""
    return row_label_to_index(row), column_to_index(column)


def index_to_row_label(row_index: int) -> str:
    """Convert zero-based row_index to row label like 'A', 'Z', 'AA'."""
    if not isinstance(row_index, int) or row_index < 0:
        raise ValueError("row_index must be a non-negative integer")
    n = row_index + 1
    letters = []
    while n > 0:
        n, rem = divmod(n - 1, 26)
        letters.append(chr(ord('A') + rem))
    return ''.join(reversed(letters))


def index_to_column(column_index: int) -> int:
    """Convert zero-based column_index to 1-based column integer."""
    if not isinstance(column_index, int) or column_index < 0:
        raise ValueError("column_index must be a non-negative integer")
    return column_index + 1


def indices_to_well(row_index: int, column_index: int) -> Tuple[str, int]:
    """Convert zero-based indices -> (row_label, 1-based column)."""
    return index_to_row_label(row_index), index_to_column(column_index)


def indices_to_well_str(row_index: int, column_index: int) -> str:
    """Convert zero-based indices -> well string like 'A1'."""
    row_label, col = indices_to_well(row_index, column_index)
    return f"{row_label}{col}"


def parse_well_designator(well: str) -> Tuple[int, int]:
    """Parse well text like 'A1' or 'AA12' to zero-based (row, col) tuple."""
    if not isinstance(well, str) or not well.strip():
        raise ValueError("Well value cannot be empty")

    clean = well.strip().upper().replace(" ", "")
    match = WELL_RE.match(clean)
    if not match:
        raise ValueError(f"Invalid well format: {well!r}")

    row_part, column_part = match.groups()
    return row_label_to_index(row_part), column_to_index(column_part)


def normalize_well_list(raw_wells: str) -> List[str]:
    """Normalize comma-delimited well list, returning sorted unique designators."""
    if not isinstance(raw_wells, str):
        raise ValueError("Wells must be provided as a comma-delimited string")

    parts = [part.strip() for part in raw_wells.split(",") if part.strip()]
    if not parts:
        raise ValueError("At least one well must be provided")

    seen = {}
    for part in parts:
        row_index, col_index = parse_well_designator(part)
        normalized = indices_to_well_str(row_index, col_index)
        seen[(row_index, col_index)] = normalized

    sorted_items = sorted(seen.items(), key=lambda item: item[0])
    return [item[1] for item in sorted_items]


def serialize_well_list(wells: Iterable[str]) -> str:
    return ",".join(wells)


def wells_fit_plate_geometry(wells: Iterable[str], num_rows: int, num_cols: int) -> bool:
    if num_rows is None or num_cols is None:
        return False

    for well in wells:
        row_index, col_index = parse_well_designator(well)
        if row_index >= int(num_rows) or col_index >= int(num_cols):
            return False
    return True


def filter_wells_for_plate(wells: Iterable[str], num_rows: int, num_cols: int) -> List[str]:
    """Return only wells that fit provided plate geometry."""
    filtered = []
    for well in wells:
        row_index, col_index = parse_well_designator(well)
        if row_index < int(num_rows) and col_index < int(num_cols):
            filtered.append(indices_to_well_str(row_index, col_index))
    return filtered
