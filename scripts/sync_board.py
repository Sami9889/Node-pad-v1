#!/usr/bin/env python3
"""Synchronize a generated NodePad board with its legacy KiCad netlist.

This tool fixes two limitations of apply_netlist.py:
1. it installs the net table and pad-to-net assignments; and
2. it replaces the unsafe reference-sorted grid with deterministic functional
   placement inside the 100 mm square board.

It intentionally does not create tracks. Routing a board with unverified pin
mappings would turn known placeholders into unsafe fabrication data.
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Net:
    code: int
    name: str
    nodes: tuple[tuple[str, str], ...]


def block_at(text: str, start: int) -> tuple[str, int]:
    depth = 0
    quoted = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif not quoted:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    return text[start:index + 1], index + 1
    raise ValueError(f"unterminated S-expression at byte {start}")


def parse_nets(text: str) -> list[Net]:
    start = text.find("(nets")
    if start < 0:
        raise ValueError("netlist has no (nets ...) section")
    section, _ = block_at(text, start)
    nets: list[Net] = []
    cursor = 0
    while True:
        match = re.search(r"\(net\s*\n", section[cursor:])
        if not match:
            break
        begin = cursor + match.start()
        raw, end = block_at(section, begin)
        code = re.search(r"\(code\s+(\d+)\)", raw)
        name = re.search(r'\(name\s+"([^"]+)"\)', raw)
        if code and name:
            nodes = tuple(re.findall(r'\(node\s*\n\s*\(ref\s+"([^"]+)"\)\s*\n\s*\(pin\s+"([^"]+)"\)', raw))
            nets.append(Net(int(code.group(1)), name.group(1), nodes))
        cursor = end
    return nets


def footprint_blocks(board: str) -> list[tuple[int, int, str, str]]:
    result = []
    cursor = 0
    while True:
        start = board.find("(footprint ", cursor)
        if start < 0:
            return result
        raw, end = block_at(board, start)
        ref = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', raw)
        if ref:
            result.append((start, end, ref.group(1), raw))
        cursor = end


def rewrite_pad_net(raw: str, pin: str, code: int, name: str) -> tuple[str, bool]:
    cursor = 0
    while True:
        match = re.search(rf'\(pad\s+"{re.escape(pin)}"\s', raw[cursor:])
        if not match:
            return raw, False
        start = cursor + match.start()
        pad, end = block_at(raw, start)
        pad = re.sub(r'\s*\(net\s+\d+\s+"[^"]*"\)', "", pad)
        replacement = pad[:-1] + f'\n\t\t(net {code} "{name}")\n\t)'
        return raw[:start] + replacement + raw[end:], True


FIXED = {
    # rear edge connectors
    "J3": (15.0, 7.0, 180.0), "J4": (36.0, 7.0, 180.0),
    "J7": (58.0, 4.0, 0.0), "J12": (76.0, 5.0, 180.0),
    # right edge USB stack
    "J8": (95.0, 24.0, 90.0), "J9": (95.0, 39.0, 90.0),
    "J10": (95.0, 54.0, 90.0), "J11": (95.0, 69.0, 90.0),
    # compute module and expansion connectors
    "J1": (43.0, 43.0, 90.0), "J2": (57.0, 43.0, 90.0),
    "J5": (49.0, 82.0, 0.0), "J6": (18.0, 46.0, 90.0),
    "J13": (69.0, 95.0, 0.0), "J15": (11.0, 95.0, 0.0),
    "BT1": (18.0, 81.0, 0.0),
    "SW1": (31.0, 96.0, 0.0), "SW2": (38.0, 96.0, 0.0),
    "MH1": (42.0, 34.0, 0.0), "MH2": (58.0, 34.0, 0.0),
    "MH3": (42.0, 52.0, 0.0), "MH4": (58.0, 52.0, 0.0),
}

CENTERS = {
    "power": (72.0, 82.0), "rtl": (35.0, 20.0), "hub": (78.0, 46.0),
    "cm5": (50.0, 44.0), "rtc": (20.0, 82.0), "hdmi": (75.0, 15.0),
    "m2m": (50.0, 74.0), "m2e": (21.0, 47.0), "poe": (15.0, 17.0),
    "io": (48.0, 91.0),
}


def group(ref: str) -> str:
    if ref in {"U3", "U4", "U5", "L1", "D6", "TP1", "TP2", "TP3", "TP4", "TP5"} or re.fullmatch(r"[CR][1-7]|C1[0-6]", ref):
        return "power"
    if ref in {"U2", "Y1"} or "RTL" in ref or "BS_J3" in ref or "BS_J4" in ref:
        return "rtl"
    if ref in {"U10", "U11", "U12", "U13", "U14", "Y_HUB"} or "HUB" in ref or "ILIM" in ref or "VB_J" in ref or "TVS_J" in ref:
        return "hub"
    if "CM5" in ref or "BOOT" in ref or "PWR_EN" in ref or "MASKROM" in ref:
        return "cm5"
    if ref in {"U7", "D_BAT"} or "RTC" in ref or "BAT" in ref or ref in {"R_SCL_PU", "R_SDA_PU", "R_INT_PU"}:
        return "rtc"
    if "HDMI" in ref or "DDC" in ref:
        return "hdmi"
    if "M2M" in ref or "PCIE0" in ref or "NVME" in ref:
        return "m2m"
    if "M2E" in ref or "PCIE1" in ref or "E_OPT" in ref:
        return "m2e"
    if "POE" in ref or ref in {"U6", "T1"}:
        return "poe"
    return "io"


def functional_positions(refs: list[str]) -> dict[str, tuple[float, float, float]]:
    positions = dict(FIXED)
    buckets: dict[str, list[str]] = {key: [] for key in CENTERS}
    for ref in sorted(refs):
        if ref not in positions:
            buckets[group(ref)].append(ref)
    # Compact local grids are a reviewable starting point. Placement is not
    # fabrication-approved until component-specific reference layouts pass.
    for key, items in buckets.items():
        cx, cy = CENTERS[key]
        columns = 6 if key in {"cm5", "hub", "io"} else 5
        pitch = 2.2
        for index, ref in enumerate(items):
            row, column = divmod(index, columns)
            x = cx + (column - (columns - 1) / 2) * pitch
            y = cy + row * pitch
            positions[ref] = (x, y, 0.0)
    return positions


def set_position(raw: str, position: tuple[float, float, float]) -> str:
    x, y, angle = position
    replacement = f"(at {x:.3f} {y:.3f}" + (f" {angle:.3f}" if angle else "") + ")"
    return re.sub(r"\(at\s+[-\d.]+\s+[-\d.]+(?:\s+[-\d.]+)?\)", replacement, raw, count=1)


def sync(board: str, nets: list[Net]) -> tuple[str, list[str]]:
    assignments = {(ref, pin): net for net in nets for ref, pin in net.nodes}
    declarations = "\n".join(f'\t(net {net.code} "{net.name}")' for net in nets)
    board = re.sub(r'\s*\(net\s+\d+\s+"[^"]*"\)', "", board)
    board = board.replace('(net 0 "")', '(net 0 "")\n' + declarations, 1)

    blocks = footprint_blocks(board)
    positions = functional_positions([ref for _, _, ref, _ in blocks])
    missing: list[str] = []
    chunks = []
    cursor = 0
    for start, end, ref, raw in blocks:
        chunks.append(board[cursor:start])
        raw = set_position(raw, positions[ref])
        for (node_ref, pin), net in assignments.items():
            if node_ref == ref:
                raw, found = rewrite_pad_net(raw, pin, net.code, net.name)
                if not found:
                    missing.append(f"{ref}.{pin} -> {net.name}")
        chunks.append(raw)
        cursor = end
    chunks.append(board[cursor:])
    normalized = re.sub(r"(?m)^[ \t]+$", "", "".join(chunks))
    return normalized, missing


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("board", type=Path)
    parser.add_argument("netlist", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    original = args.board.read_text()
    nets = parse_nets(args.netlist.read_text())
    updated, missing = sync(original, nets)
    assigned = sum(len(net.nodes) for net in nets) - len(missing)
    print(f"nets={len(nets)} assigned_pads={assigned} missing_pads={len(missing)}")
    for item in missing[:30]:
        print(f"MISSING {item}")
    if args.check:
        if updated != original:
            raise SystemExit("board is not synchronized; run without --check")
    else:
        args.board.write_text(updated)


if __name__ == "__main__":
    main()
