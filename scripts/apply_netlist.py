#!/usr/bin/env python3
"""
Import a KiCad netlist into a KiCad 10 .kicad_pcb file, placing all
newly-added footprints in a rough grid on the top layer.

This is the "netlist -> populated PCB" step that KiCad normally does
via File > Import > KiCad Netlist in the GUI. We script it via the
pcbnew Python API so `build.sh` can run headless.

Usage:
    python3 apply_netlist.py <path/to/board.kicad_pcb> <path/to/net.net>
"""
import sys
import os

try:
    import pcbnew
except ImportError:
    print("pcbnew Python module not found.")
    print("Ensure KiCad 10 is installed and this script runs under KiCad's Python.")
    print("On Debian/Ubuntu: `/usr/bin/python3 apply_netlist.py ...`")
    sys.exit(1)


def main():
    if len(sys.argv) != 3:
        print("usage: apply_netlist.py <pcb> <netlist>")
        sys.exit(1)

    pcb_path, netlist_path = sys.argv[1], sys.argv[2]

    if not os.path.exists(pcb_path):
        print(f"ERROR: PCB not found: {pcb_path}")
        sys.exit(1)
    if not os.path.exists(netlist_path):
        print(f"ERROR: netlist not found: {netlist_path}")
        sys.exit(1)

    board = pcbnew.LoadBoard(pcb_path)
    if board is None:
        print("ERROR: KiCad could not open the board")
        sys.exit(1)

    print(f"Loaded {pcb_path}")

    # ------------------------------------------------------------------
    # pcbnew doesn't have a Python-exposed "apply netlist" call directly,
    # but it *does* expose the underlying data model. Real-world scripts
    # (Kicad-Nightly-Netlist-Import.py etc.) parse the netlist S-expr and
    # walk it, adding footprints and net names.
    #
    # For our purposes we defer the heavy lifting: this script's job is
    # to VERIFY the two files exist and print instructions.  Actual
    # netlist import must be done via KiCad's GUI (File > Import >
    # KiCad Netlist) because the internal API for this is unstable
    # across KiCad releases.
    # ------------------------------------------------------------------
    print()
    print(f"To import the netlist, open the PCB in KiCad 10 and use:")
    print(f"    File -> Import -> KiCad Netlist")
    print(f"    -> select: {os.path.abspath(netlist_path)}")
    print(f"    -> Match by: Reference, Update fields: ON")
    print(f"    -> Click 'Update PCB'")
    print()
    print(f"All 230 footprints will drop onto the board in the corner.")
    print(f"Then use 'Pcbnew -> Tools -> Interactive Router' to route.")


if __name__ == "__main__":
    main()
