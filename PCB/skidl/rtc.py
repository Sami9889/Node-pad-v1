"""
NodePad — RTC + coin cell backup

  DS3231MZ+ I²C real-time clock (TCXO, ±5 ppm) with CR2032 coin-cell backup.
  Talks to CM5 on I²C0 (shared with GPIO header).
"""

import os
os.environ.setdefault("KICAD_SYMBOL_DIR", "/opt/kicad-libs/symbols")
os.environ.setdefault("KICAD9_SYMBOL_DIR", "/opt/kicad-libs/symbols")

from skidl import Part, Net, TEMPLATE, set_default_tool, KICAD9

set_default_tool(KICAD9)

R = Part("Device", "R", dest=TEMPLATE, footprint="Resistor_SMD:R_0402_1005Metric")
C = Part("Device", "C", dest=TEMPLATE, footprint="Capacitor_SMD:C_0402_1005Metric")


def build(V3P3, GND, SDA, SCL, INT_N=None):
    """Instantiate the RTC block.  Nets passed in from the top-level design."""

    # ------------------------------------------------------------------
    # U7 : DS3231MZ+  (SOIC-8; I²C, TCXO, ±5ppm)
    # LCSC C107373
    # Pins (SOIC-8):
    #   1  V_BAT
    #   2  N.C.
    #   3  N.C.
    #   4  GND
    #   5  SDA
    #   6  SCL
    #   7  INT/SQW (open-drain)
    #   8  VCC
    # ------------------------------------------------------------------
    U7 = Part("Timer_RTC", "DS3231MZ",
              value="DS3231MZ+",
              ref="U7",
              footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm")

    # ------------------------------------------------------------------
    # BT1 : CR2032 SMD holder (Keystone 3002 style)
    # ------------------------------------------------------------------
    BT1 = Part("Device", "Battery_Cell",
               value="CR2032",
               ref="BT1",
               footprint="Battery:BatteryHolder_Keystone_3002_1x2032")

    VBAT = Net("V_BAT")

    # Battery -> VBAT pin, with a series diode + decoupling
    # Small Schottky prevents backfeed into VCC when V3P3 is up
    D_bat = Part("Device", "D_Schottky",
                 value="BAT54",
                 ref="D_BAT",
                 footprint="Diode_SMD:D_SOD-323")
    D_bat[1] += BT1[1]     # + terminal
    D_bat[2] += VBAT
    BT1[2]   += GND        # - terminal

    # Also allow V3P3 to charge/hold the battery bus through a large resistor
    # (DS3231 has internal trickle charger for supercap; disable for CR2032)
    # We keep V_BAT purely from CR2032 via BAT54.

    C_bat = C(value="100nF", ref="C_BAT_1"); C_bat[1] += VBAT; C_bat[2] += GND

    # DS3231 pins (KiCad symbol pin names)
    U7["VCC"] += V3P3
    U7["GND"] += GND
    U7["VBAT"] += VBAT
    U7["SDA"] += SDA
    U7["SCL"] += SCL

    # INT/SQW is open-drain, needs external pull-up (share with I²C bus)
    if INT_N is not None:
        U7["~{INT}/SQW"] += INT_N
        R_int_pu = R(value="10k", ref="R_INT_PU")
        R_int_pu[1] += V3P3; R_int_pu[2] += INT_N

    # VCC decoupling
    C_vcc = C(value="100nF", ref="C_RTC_1"); C_vcc[1] += V3P3; C_vcc[2] += GND
    C_vcc2 = C(value="1uF",  ref="C_RTC_2"); C_vcc2[1] += V3P3; C_vcc2[2] += GND

    # I²C pull-ups (4.7k typical for 400kHz)
    R_sda = R(value="4.7k", ref="R_SDA_PU")
    R_sda[1] += V3P3; R_sda[2] += SDA
    R_scl = R(value="4.7k", ref="R_SCL_PU")
    R_scl[1] += V3P3; R_scl[2] += SCL

    return U7
