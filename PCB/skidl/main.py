"""
NodePad — Main schematic composition.

Combines the sub-blocks (power tree, RTC, user I/O) into a single design
and emits the KiCad netlist.

The complex sub-blocks that need careful datasheet review (Radxa CM5 SoM
connector wiring, RTL8125 with its magnetics, GL3523 USB hub, M.2 slots,
HDMI ESD, PoE input) are stubbed for now — they are the biggest chunk of
engineering work and belong in dedicated review sessions, not automated
generation.

Run:
    KICAD_SYMBOL_DIR=/opt/kicad-libs/symbols \\
    python3 main.py

Outputs:
    ./netlists/nodepad.net       (KiCad netlist, importable via
                                  Pcbnew ► File ► Import ► KiCad Netlist)
"""

import os
os.environ.setdefault("KICAD_SYMBOL_DIR", "/opt/kicad-libs/symbols")
os.environ.setdefault("KICAD9_SYMBOL_DIR", "/opt/kicad-libs/symbols")

from skidl import Net, generate_netlist, ERC, set_default_tool, KICAD9

set_default_tool(KICAD9)


# ---------------------------------------------------------------------------
# Top-level nets (shared across all sub-blocks)
# ---------------------------------------------------------------------------
GND   = Net("GND"); GND.drive = 3

# Power rails
VBUS_USB = Net("VBUS_USB")     # raw 5V from USB-C
VIN_12V  = Net("VIN_12V")      # after CH224K PD sink
V5       = Net("+5V")          # MP2315 output
V3P3     = Net("+3V3_AUX")     # AP2112 output

# I²C bus (RTC + GPIO header)
I2C_SDA = Net("I2C0_SDA")
I2C_SCL = Net("I2C0_SCL")

# ---------------------------------------------------------------------------
# 1) Power tree
# ---------------------------------------------------------------------------
# Just importing power_tree.py runs it top-to-bottom and instantiates all
# power parts. It uses its own GND/nets — we don't need to pass them in.
# For a full production merge we would refactor power_tree.py into a
# build() function too; for now we treat this file as the primary entry.

import power_tree  # noqa: F401  (side effect: instantiates all power parts)


# ---------------------------------------------------------------------------
# 2) RTC
# ---------------------------------------------------------------------------
# Reach into power_tree's nets by name (SKiDL de-duplicates by net name)
V3P3_pt = Net.get("+3V3_AUX")
GND_pt  = Net.get("GND")

import rtc
rtc.build(V3P3=V3P3_pt, GND=GND_pt, SDA=I2C_SDA, SCL=I2C_SCL, INT_N=Net("RTC_INT_N"))


# ---------------------------------------------------------------------------
# 3) User I/O
# ---------------------------------------------------------------------------
V5_pt = Net.get("+5V")

import user_io as io_block

io_block.build(
    V3P3=V3P3_pt,
    V5=V5_pt,
    GND=GND_pt,
    SIGNALS={
        # These are the placeholder signal names that will get wired to
        # the Radxa CM5 SoM connector (J1/J2) when that sub-block is
        # authored.  They already show up in the netlist as unresolved
        # nets that are easy to find in Pcbnew ratsnest.
        "RESET_N":   Net("CM5_RUN_N"),
        "RECOVERY":  Net("CM5_MASKROM"),
        "LED_SYS":   Net("CM5_GPIO_STATUS"),
        "LED_LNK1":  Net("PHY1_LED_ACT"),
        "LED_LNK2":  Net("PHY2_LED_ACT"),
        "LED_NVME":  Net("NVME_ACT_N"),
        "FAN_TACH":  Net("FAN_TACH"),
        "FAN_PWM":   Net("FAN_PWM"),
    },
)


# ---------------------------------------------------------------------------
# TODO (next authoring sessions)
# ---------------------------------------------------------------------------
# - cm5.py       : Radxa CM5 SoM connectors J1/J2 (2 x DF40C-100DS-0.4V),
#                  breaks out every power/signal pin per Radxa datasheet
# - ethernet.py  : RJ45 #1 (CM5 native GbE via magnetics), RJ45 #2 (RTL8125)
# - usb_hub.py   : GL3523 USB 3.0 hub + 4x USB-A + TPS2553 per-port switches
# - m2.py        : M.2 M-key NVMe (2280) + M.2 E-key WiFi (2230), PCIe routing
# - hdmi.py      : HDMI Type-A jack + PESD ESD array on 4 diff pairs
# - poe.py       : Optional PoE PD circuit (DNP by default)


# ---------------------------------------------------------------------------
# Emit netlist
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    os.makedirs("netlists", exist_ok=True)
    ERC()
    generate_netlist(file_="netlists/nodepad.net")
    print("[OK] Combined netlist -> netlists/nodepad.net")
