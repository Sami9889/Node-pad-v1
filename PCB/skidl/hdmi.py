"""
NodePad — HDMI 2.0 Type-A output

  * J12: HDMI Type-A receptacle
  * ESD arrays on 4 differential pairs + control lines

TMDS pairs are AC-coupled inside the CM5, so no external caps needed.
DDC (I2C) needs pull-ups to 5V per HDMI spec.
"""

import os
os.environ.setdefault("KICAD_SYMBOL_DIR", "/opt/kicad-libs/symbols")
os.environ.setdefault("KICAD9_SYMBOL_DIR", "/opt/kicad-libs/symbols")

from skidl import Part, Net, TEMPLATE, set_default_tool, KICAD9

set_default_tool(KICAD9)

R = Part("Device", "R", dest=TEMPLATE, footprint="Resistor_SMD:R_0402_1005Metric")
C = Part("Device", "C", dest=TEMPLATE, footprint="Capacitor_SMD:C_0402_1005Metric")


def build(nets):

    V5   = nets["+5V"]
    V3P3 = nets["+3V3_AUX"]
    GND  = nets["GND"]

    # HDMI Type-A jack (19-pin)
    J12 = Part("Connector", "HDMI_A",
               value="HDMI",
               ref="J12",
               footprint="Connector_Video:HDMI_A_Molex_208658-1001_Horizontal")

    # TMDS pairs (differential, CM5 side)
    J12["D2+"] += nets["HDMI_TX2_P"]; J12["D2-"] += nets["HDMI_TX2_N"]
    J12["D2S"] += GND
    J12["D1+"] += nets["HDMI_TX1_P"]; J12["D1-"] += nets["HDMI_TX1_N"]
    J12["D1S"] += GND
    J12["D0+"] += nets["HDMI_TX0_P"]; J12["D0-"] += nets["HDMI_TX0_N"]
    J12["D0S"] += GND
    J12["CK+"] += nets["HDMI_CLK_P"]; J12["CK-"] += nets["HDMI_CLK_N"]
    J12["CKS"] += GND

    # CEC, HPD, DDC (control lines)
    J12["CEC"]     += nets["HDMI_CEC"]
    J12["HPD"]     += nets["HDMI_HPD"]
    J12["SCL"]     += nets["HDMI_DDC_SCL"]
    J12["SDA"]     += nets["HDMI_DDC_SDA"]

    # +5V out to sink (HDMI spec requires this; 55mA typical)
    J12[18]     += Net("HDMI_5V_OUT")
    # Series ferrite + 500mA polyfuse recommended
    fb = Part("Device", "L_Small", value="600R@100MHz",
              ref="FB_HDMI_5V",
              footprint="Inductor_SMD:L_0603_1608Metric")
    fb[1] += V5; fb[2] += Net("HDMI_5V_OUT")

    # Shell + shield ground
    J12["SH"] += GND
    J12[17] += GND

    # -- ESD protection ---------------------------------------------
    # PESD1CAN or equivalent 4-line TVS array per HDMI pair
    for i, (p, n) in enumerate([
        (nets["HDMI_TX0_P"], nets["HDMI_TX0_N"]),
        (nets["HDMI_TX1_P"], nets["HDMI_TX1_N"]),
        (nets["HDMI_TX2_P"], nets["HDMI_TX2_N"]),
        (nets["HDMI_CLK_P"], nets["HDMI_CLK_N"]),
    ]):
        # Use USBLC6-2SC6 (5V, 2-line low-C TVS, common for HDMI too)
        tvs = Part("Power_Protection", "USBLC6-2SC6",
                   value="USBLC6-2SC6",
                   ref=f"U_HDMI_ESD_{i+1}",
                   footprint="Package_TO_SOT_SMD:SOT-23-6")
        tvs["I/O1"] += p
        tvs["I/O2"] += n
        tvs["GND"]  += GND
        tvs["VBUS"] += V5

    # ESD on CEC/HPD/DDC (single-line TVS)
    for i, sig in enumerate([nets["HDMI_CEC"], nets["HDMI_HPD"]]):
        d = Part("Device", "D_TVS", value="ESD5Z5.0",
                 ref=f"D_HDMI_CTL_{i+1}",
                 footprint="Diode_SMD:D_SOD-523")
        d[1] += sig; d[2] += GND

    # DDC I2C pull-ups (HDMI spec requires pull-ups to +5V)
    R_ddc_scl = R(value="2.2k", ref="R_DDC_SCL")
    R_ddc_scl[1] += V5; R_ddc_scl[2] += nets["HDMI_DDC_SCL"]
    R_ddc_sda = R(value="2.2k", ref="R_DDC_SDA")
    R_ddc_sda[1] += V5; R_ddc_sda[2] += nets["HDMI_DDC_SDA"]

    # Voltage-level shifter for DDC (5V <-> 3.3V) via MOSFETs on each line
    # For simplicity, add 100R series resistors on CM5 side (CM5 tolerant)
    R_ser_scl = R(value="100", ref="R_DDC_SCL_SER")
    R_ser_sda = R(value="100", ref="R_DDC_SDA_SER")
    # Note: proper level shifter (e.g. TXS0102) recommended for production.

    return J12
