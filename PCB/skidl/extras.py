"""
NodePad — Extras: heatsink mount, HDMI DDC level shifter, extra decoupling.

Everything in this file is stuff you'd want on a real production board
but doesn't fit cleanly into any single sub-block.
"""

import os
os.environ.setdefault("KICAD_SYMBOL_DIR", "/opt/kicad-libs/symbols")
os.environ.setdefault("KICAD9_SYMBOL_DIR", "/opt/kicad-libs/symbols")

from skidl import Part, Net, TEMPLATE, set_default_tool, KICAD9

set_default_tool(KICAD9)

R = Part("Device", "R", dest=TEMPLATE, footprint="Resistor_SMD:R_0402_1005Metric")
C = Part("Device", "C", dest=TEMPLATE, footprint="Capacitor_SMD:C_0402_1005Metric")
C_BULK = Part("Device", "C", dest=TEMPLATE, footprint="Capacitor_SMD:C_0805_2012Metric")


def build(nets):
    V5   = nets["+5V"]
    V3P3 = nets["+3V3_AUX"]
    GND  = nets["GND"]

    # ------------------------------------------------------------------
    # HDMI DDC (I²C) level shifter: 3.3V (CM5 side) <-> 5V (HDMI DDC side)
    # Two NMOS-based bidirectional shifters (BSS138 x2) form a passive
    # translator — cheap, works up to 400kHz easily.
    # ------------------------------------------------------------------
    for i, sig in enumerate(["HDMI_DDC_SDA", "HDMI_DDC_SCL"]):
        Q = Part("Device", "Q_NMOS",
                 value="BSS138",
                 ref=f"Q_DDC_{i+1}",
                 footprint="Package_TO_SOT_SMD:SOT-23")
        # G tied to 3.3V through 10k, S = CM5 side, D = HDMI 5V side
        R_g = R(value="10k", ref=f"R_DDC_G_{i+1}")
        R_g[1] += V3P3; R_g[2] += Q["G"]
        # Low side (3.3V, CM5)
        Q["S"] += nets[sig]
        R_lo = R(value="10k", ref=f"R_DDC_LO_{i+1}")
        R_lo[1] += V3P3; R_lo[2] += nets[sig]
        # High side (5V, HDMI sink)
        Q["D"] += Net(f"{sig}_5V")
        R_hi = R(value="10k", ref=f"R_DDC_HI_{i+1}")
        R_hi[1] += V5; R_hi[2] += Net(f"{sig}_5V")

    # ------------------------------------------------------------------
    # Heatsink mounting posts (4x M2.5 mounting holes near CM5)
    # These are unplated NPTH holes on the PCB - the thermal solution is
    # a screw-on heatsink pressing down onto the CM5's SoC through a
    # thermal pad.  Modeled as mechanical footprints with no electrical
    # connection.
    # ------------------------------------------------------------------
    for i in range(4):
        mh = Part("Mechanical", "MountingHole",
                  value="M2.5 heatsink",
                  ref=f"MH{i+1}",
                  footprint="MountingHole:MountingHole_2.7mm_M2.5")
        # No electrical net — mechanical only
        try:
            mh[1] += GND
        except Exception:
            pass  # some MountingHole symbols have no pins

    # Also a keep-out label for the CM5 heatsink footprint (large square)
    # -> handled visually in PCB layout, not in schematic

    # ------------------------------------------------------------------
    # Belt-and-braces extra decoupling
    # Every power rail gets more 100nF + 10uF pairs distributed near the
    # main consumers.
    # ------------------------------------------------------------------
    for rail_name, rail_net, hf_count, bulk_count in [
        ("+5V",      V5,   12, 4),
        ("+3V3_AUX", V3P3, 10, 3),
    ]:
        for i in range(hf_count):
            c = C(value="100nF", ref=f"C_DEC_{rail_name[1:]}_{i+1:02d}")
            c[1] += rail_net; c[2] += GND
        for i in range(bulk_count):
            c = C_BULK(value="10uF", ref=f"C_BLK_{rail_name[1:]}_{i+1:02d}")
            c[1] += rail_net; c[2] += GND

    # ------------------------------------------------------------------
    # Extra ferrite beads on power inputs to sensitive analog blocks
    # ------------------------------------------------------------------
    for i, name in enumerate(["AVDD_HDMI", "AVDD_PCIE", "AVDD_ETH0", "AVDD_ETH1"]):
        fb = Part("Device", "L_Small",
                  value="600R@100MHz",
                  ref=f"FB_AVDD_{i+1}",
                  footprint="Inductor_SMD:L_0603_1608Metric")
        fb[1] += V3P3
        fb[2] += Net(name)
        # Local bypass on filtered rail
        c1 = C(value="100nF", ref=f"C_AVDD_HF_{i+1}"); c1[1] += Net(name); c1[2] += GND
        c2 = C_BULK(value="10uF", ref=f"C_AVDD_BULK_{i+1}"); c2[1] += Net(name); c2[2] += GND

    # ------------------------------------------------------------------
    # Board-level EMI cap between chassis and system ground (1nF, 2kV)
    # ------------------------------------------------------------------
    c_emi = Part("Device", "C", value="1nF/2kV",
                 ref="C_EMI",
                 footprint="Capacitor_SMD:C_1210_3225Metric")
    c_emi[1] += GND; c_emi[2] += Net("CHASSIS_GND")
