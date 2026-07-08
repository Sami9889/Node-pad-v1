"""
NodePad-Net — SFP cage for 1G fiber uplink

  * J20: 1× standard SFP cage (host connector)
  * Talks to CM5 via SGMII (Serial Gigabit Media Independent Interface)
    on the CM5's spare GbE MAC (the one not used for RJ45 #1).
  * Alternatively, over PCIe using an SFP-to-PCIe transceiver bridge
    (but that costs $$$ so we go SGMII).

REVIEW BEFORE FAB:
  - Confirm CM5 exposes SGMII pins (not just RGMII).  Some Radxa CM5
    variants may not — check the current datasheet.  If SGMII isn't
    available, this variant needs a discrete PHY chip (e.g. VSC8221
    or 88E1512) between CM5's RGMII and the SFP.
  - SFP MOD_ABS + LOS + RS0/RS1 need GPIO pins.
  - I²C0 is shared with SFP EEPROM read (per SFF-8472).
"""

import os
os.environ.setdefault("KICAD_SYMBOL_DIR", "/opt/kicad-libs/symbols")
os.environ.setdefault("KICAD9_SYMBOL_DIR", "/opt/kicad-libs/symbols")

from skidl import Part, Net, TEMPLATE, set_default_tool, KICAD9

set_default_tool(KICAD9)

R = Part("Device", "R", dest=TEMPLATE, footprint="Resistor_SMD:R_0402_1005Metric")
C = Part("Device", "C", dest=TEMPLATE, footprint="Capacitor_SMD:C_0402_1005Metric")


def build(nets):
    """SFP cage with control signals + 3.3V supply."""
    V3P3 = nets["+3V3_AUX"]
    V5   = nets["+5V"]
    GND  = nets["GND"]

    # SFP cage: standard 20-pin edge-connector footprint.
    # KiCad std lib has "Amphenol_10105647-XXXXX" — use generic.
    # Model as Conn_01x20 placeholder.
    J20 = Part("Connector_Generic", "Conn_01x20",
               value="SFP-CAGE",
               ref="J20",
               footprint="Connector_Card:SFP_Molex_74441-0011")

    # ----- SFP pinout (per SFF-8431 / SFF-8472) ------------------------
    #  1  VeeT   (transmit GND)
    #  2  TX_FAULT
    #  3  TX_DISABLE
    #  4  MOD_DEF2 / SDA
    #  5  MOD_DEF1 / SCL
    #  6  MOD_DEF0 (MOD_ABS)   (module-present, active low)
    #  7  RS0 / SPEED_SEL
    #  8  LOS (loss of signal)
    #  9  RS1
    # 10  VeeR   (receive GND)
    # 11  VeeR
    # 12  RD-
    # 13  RD+
    # 14  VeeR
    # 15  VccR   (+3.3V, receive supply)
    # 16  VccT   (+3.3V, transmit supply)
    # 17  VeeT
    # 18  TD+
    # 19  TD-
    # 20  VeeT
    for gpin in [1, 10, 11, 14, 17, 20]:
        J20[gpin] += GND

    for vpin in [15, 16]:
        J20[vpin] += V3P3

    # Data pairs (differential, SGMII-like)
    J20[13] += nets["SFP_RX_P"];   J20[12] += nets["SFP_RX_N"]
    J20[18] += nets["SFP_TX_P"];   J20[19] += nets["SFP_TX_N"]

    # Control lines (all open-drain, need pull-ups to 3.3V)
    ctrl_signals = {
        2: ("SFP_TX_FAULT",   True),   # input to CM5
        3: ("SFP_TX_DISABLE", False),  # output from CM5
        4: ("SFP_MOD_SDA",    True),
        5: ("SFP_MOD_SCL",    True),
        6: ("SFP_MOD_ABS_N",  True),
        7: ("SFP_RS0",        False),
        8: ("SFP_LOS",        True),
        9: ("SFP_RS1",        False),
    }
    for pin, (netname, needs_pu) in ctrl_signals.items():
        n = Net(netname)
        J20[pin] += n
        if needs_pu:
            r = R(value="4.7k", ref=f"R_SFP_{netname[4:]}_PU")
            r[1] += V3P3; r[2] += n

    # ----- 3.3V decoupling near SFP -----------------------------------
    for i in range(4):
        c = C(value="100nF", ref=f"C_SFP_HF_{i+1}")
        c[1] += V3P3; c[2] += GND
    c_bulk = Part("Device", "C", value="10uF", ref="C_SFP_BULK",
                  footprint="Capacitor_SMD:C_0603_1608Metric")
    c_bulk[1] += V3P3; c_bulk[2] += GND

    # ----- Ferrite bead between system 3.3V and SFP VccR/VccT ---------
    fb = Part("Device", "L_Small", value="600R@100MHz",
              ref="FB_SFP",
              footprint="Inductor_SMD:L_0603_1608Metric")
    fb[1] += V3P3
    fb[2] += Net("SFP_3V3_FILT")
    # Alt-route J20[15] and J20[16] through this filtered rail if desired
    # (For simplicity, we've tied them directly to V3P3 above.)

    # ----- AC-coupling caps on SGMII pairs (SFP spec requires) --------
    # Typically 0.1uF between CM5 side and SFP side of each diff line.
    # We put these on the CM5 side of the pairs, before the SFP jack.
    for pname in ["SFP_TX_P", "SFP_TX_N", "SFP_RX_P", "SFP_RX_N"]:
        # Net name convention: CM5_<PN> -> AC cap -> <PN> to SFP
        cm5_side = Net(f"CM5_{pname}")
        c_ac = C(value="100nF", ref=f"C_AC_{pname}")
        c_ac[1] += cm5_side; c_ac[2] += nets[pname]

    return J20
