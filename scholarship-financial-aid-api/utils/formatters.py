"""Formatting and ID-generation helpers ([Unit II] String Manipulations)."""

import re


def format_money(amount):
    """Format a number as money text: 25000 -> '25,000.00'.

    Uses an f-string with the thousands-separator format spec.
    """
    if amount is None:
        return "0.00"
    return f"{amount:,.2f}"


def next_sequential_id(existing_ids, prefix):
    """Generate the next sequential ID, e.g. ['A001'..'A006'] + 'A' -> 'A007'.

    Used when the client does not supply a primary key. The zero padding of
    the widest existing ID is kept ('S001' -> 'S006').

    [Unit II] Control Flow: the while loop defensively skips any candidate
    ID that is somehow already taken; a set is used for fast lookups.
    """
    numbers = []
    width = 2  # minimum padding, e.g. 'T04'
    for value in existing_ids:
        match = re.fullmatch(r"([A-Za-z]*)(\d+)", str(value).strip())
        if match:
            numbers.append(int(match.group(2)))
            width = max(width, len(match.group(2)))

    next_number = max(numbers) + 1 if numbers else 1
    candidate = f"{prefix}{str(next_number).zfill(width)}"  # zfill = padding

    taken = set(existing_ids)  # [Unit II] set for O(1) membership tests
    while candidate in taken:  # never hand out an ID that already exists
        next_number += 1
        candidate = f"{prefix}{str(next_number).zfill(width)}"

    return candidate
