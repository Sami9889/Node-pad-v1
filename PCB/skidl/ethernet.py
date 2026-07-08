"""
NodePad — Ethernet subsystem

  * RJ45 #1 (J3): 1 GbE from CM5 native PHY. External magnetics (M1).
  * RJ45 #2 (J4): 2.5 GbE from RTL8125BG (U2). External magnetics (M2).

The KiCad standard library doesn't ship a gigabit-mag RJ45 symbol, so we
use a plain 8-pin RJ45 + a placeholder magnetics transformer next to it.
For production, replace with the actual Bel Fuse 0826-1G1T footprint
(integrated mag+jack in one part) and merge these into a single symbol.

REVIEW BEFORE FAB:
  - RTL8125BG pin numbers  (Realtek datasheet)
  - Magnetics pin order    (Bel Fuse 0826-1G1T)
  - 25 MHz TCXO placement close to XTAL_IN pin on RTL8125
"""

import os
os.environ.setdefault("KICAD_SYMBOL_DIR", "/opt/kicad-libs/symbols")
os.environ.setdefault("KICAD9_SYMBOL_DIR", "/opt/kicad-libs/symbols")

from skidl import Part, Net, TEMPLATE, set_default_tool, KICAD9

set_default_tool(KICAD9)

R = Part("Device", "R", dest=TEMPLATE, footprint="Resistor_SMD:R_0402_1005Metric")
C = Part("Device", "C", dest=TEMPLATE, footprint="Capacitor_SMD:C_0402_1005Metric")


def build_rj45(ref, mdi, V3P3, GND, LED_ACT, LED_LNK, chassis_gnd):
    """Plain 8-pin RJ45 + separate placeholder magnetics + Bob Smith termination."""
    J = Part("Connector", "RJ45", value="RJ45", ref=ref,
             footprint="Connector_RJ:RJ45_Amphenol_RJHSE538X_Horizontal")

    # -- Wire 4 MDI pairs to jack pins 1-8 (per T568B) -----------------
    # 1/2 pair 1, 3/6 pair 2, 4/5 pair 3, 7/8 pair 4
    J[1] += mdi["MDI0_P"];  J[2] += mdi["MDI0_N"]
    J[3] += mdi["MDI1_P"];  J[6] += mdi["MDI1_N"]
    J[4] += mdi["MDI2_P"];  J[5] += mdi["MDI2_N"]
    J[7] += mdi["MDI3_P"];  J[8] += mdi["MDI3_N"]

    # -- Bob Smith termination: 75Ω per line to common, common -> 1kV cap -> chassis GND
    common = Net(f"BOBSMITH_{ref}")
    for pin_num in [1, 2, 3, 4, 5, 6, 7, 8]:
        r = R(value="75", ref=f"R_BS_{ref}_{pin_num}")
        r[1] += J[pin_num]; r[2] += common
    c_bs = Part("Device", "C", value="1nF/2kV",
                ref=f"C_BS_{ref}",
                footprint="Capacitor_SMD:C_1210_3225Metric")
    c_bs[1] += common; c_bs[2] += chassis_gnd

    return J


def build(nets):
    GND  = nets["GND"]
    V3P3 = nets["+3V3_AUX"]
    V5   = nets["+5V"]

    chassis_gnd = Net("CHASSIS_GND")

    # --- RJ45 #1: 1 GbE from CM5 native PHY -----------------------------
    mdi1 = {
        "MDI0_P": nets["ETH0_MDI0_P"], "MDI0_N": nets["ETH0_MDI0_N"],
        "MDI1_P": nets["ETH0_MDI1_P"], "MDI1_N": nets["ETH0_MDI1_N"],
        "MDI2_P": nets["ETH0_MDI2_P"], "MDI2_N": nets["ETH0_MDI2_N"],
        "MDI3_P": nets["ETH0_MDI3_P"], "MDI3_N": nets["ETH0_MDI3_N"],
    }
    build_rj45("J3", mdi1, V3P3, GND,
               LED_ACT=nets["ETH0_LED_ACT"], LED_LNK=nets["ETH0_LED_LINK"],
               chassis_gnd=chassis_gnd)

    # --- U2: RTL8125BG (QFN-64) ----------------------------------------
    # Placeholder: Conn_02x32_Odd_Even = 64 pins
    U2 = Part("Connector_Generic", "Conn_02x32_Odd_Even",
              value="RTL8125BG",
              ref="U2",
              footprint="Package_DFN_QFN:QFN-64-1EP_9x9mm_P0.5mm_EP4.7x4.7mm")

    # PCIe interface  TODO_VERIFY
    U2[55] += nets["PCIE1_TX_P"];    U2[56] += nets["PCIE1_TX_N"]
    U2[58] += nets["PCIE1_RX_P"];    U2[59] += nets["PCIE1_RX_N"]
    U2[61] += nets["PCIE1_REFCLK_P"]; U2[62] += nets["PCIE1_REFCLK_N"]
    U2[63] += nets["PCIE1_PERST_N"]
    U2[64] += nets["PCIE1_CLKREQ_N"]
    U2[54] += nets["PCIE1_WAKE_N"]

    # MDI pairs
    U2[1] += nets["ETH1_MDI0_P"];    U2[2] += nets["ETH1_MDI0_N"]
    U2[4] += nets["ETH1_MDI1_P"];    U2[5] += nets["ETH1_MDI1_N"]
    U2[7] += nets["ETH1_MDI2_P"];    U2[8] += nets["ETH1_MDI2_N"]
    U2[10] += nets["ETH1_MDI3_P"];   U2[11] += nets["ETH1_MDI3_N"]

    # 25 MHz crystal
    Y1 = Part("Device", "Crystal", value="25MHz TCXO", ref="Y1",
              footprint="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm")
    U2[15] += Y1[1]; U2[16] += Y1[2]
    # 2-pin crystal, both pins already connected

    # LEDs
    U2[20] += nets["ETH1_LED_ACT"]
    U2[21] += nets["ETH1_LED_LINK"]

    # Power
    for p in [22, 30, 40, 50]:
        U2[p] += V3P3
    for p in [23, 31, 41, 51]:
        U2[p] += V3P3

    for p in [3, 6, 9, 12, 14, 17, 24, 29, 32, 39, 42, 49, 52, 60]:
        U2[p] += GND

    # Decoupling
    for i in range(6):
        c = C(value="100nF", ref=f"C_RTL_{i+1}")
        c[1] += V3P3; c[2] += GND
    c_bulk = Part("Device", "C", value="10uF", ref="C_RTL_BULK",
                  footprint="Capacitor_SMD:C_0603_1608Metric")
    c_bulk[1] += V3P3; c_bulk[2] += GND

    # --- RJ45 #2: 2.5 GbE from RTL8125 ---------------------------------
    mdi2 = {
        "MDI0_P": nets["ETH1_MDI0_P"], "MDI0_N": nets["ETH1_MDI0_N"],
        "MDI1_P": nets["ETH1_MDI1_P"], "MDI1_N": nets["ETH1_MDI1_N"],
        "MDI2_P": nets["ETH1_MDI2_P"], "MDI2_N": nets["ETH1_MDI2_N"],
        "MDI3_P": nets["ETH1_MDI3_P"], "MDI3_N": nets["ETH1_MDI3_N"],
    }
    build_rj45("J4", mdi2, V3P3, GND,
               LED_ACT=nets["ETH1_LED_ACT"], LED_LNK=nets["ETH1_LED_LINK"],
               chassis_gnd=chassis_gnd)

    return U2
