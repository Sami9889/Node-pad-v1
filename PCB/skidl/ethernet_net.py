"""
NodePad-Net — Second 2.5 GbE port (for the networking-focused variant)

  * U15: Second RTL8125BG (same chip as U2 in ethernet.py, but a different
         placement — this one hangs off the CM5's PCIe1 lane while the
         original RTL8125 stays on Combo0 shared with NVMe).
  * J21: RJ45 #3 (2.5G)
  * Bob-Smith termination + magnetics same as ethernet.py

Because CM5's PCIe1 is only x1, we effectively give up the M.2 E-key slot
in the -Net variant (WiFi is redundant on a router/switch node anyway).

REVIEW BEFORE FAB:
  - RTL8125 requires unique PCIe device address — hardware address bits
    on RTL8125 (BS0, BS1) must be different from U2.
  - EEPROM (93C46 or 25040) is optional but recommended for permanent
    MAC address storage per NIC.
"""

import os
os.environ.setdefault("KICAD_SYMBOL_DIR", "/opt/kicad-libs/symbols")
os.environ.setdefault("KICAD9_SYMBOL_DIR", "/opt/kicad-libs/symbols")

from skidl import Part, Net, TEMPLATE, set_default_tool, KICAD9

set_default_tool(KICAD9)

R = Part("Device", "R", dest=TEMPLATE, footprint="Resistor_SMD:R_0402_1005Metric")
C = Part("Device", "C", dest=TEMPLATE, footprint="Capacitor_SMD:C_0402_1005Metric")


def build(nets):
    V3P3 = nets["+3V3_AUX"]
    GND  = nets["GND"]

    # Second RTL8125BG on PCIe1
    U15 = Part("Connector_Generic", "Conn_02x32_Odd_Even",
               value="RTL8125BG-2",
               ref="U15",
               footprint="Package_DFN_QFN:QFN-64-1EP_9x9mm_P0.5mm_EP4.7x4.7mm")

    # PCIe interface (uses PCIE1_* which was going to M.2 E-key)
    # TODO_VERIFY every pin against Realtek RTL8125BG datasheet
    U15[55] += nets["PCIE1_TX_P"];    U15[56] += nets["PCIE1_TX_N"]
    U15[58] += nets["PCIE1_RX_P"];    U15[59] += nets["PCIE1_RX_N"]
    U15[61] += nets["PCIE1_REFCLK_P"]; U15[62] += nets["PCIE1_REFCLK_N"]
    U15[63] += nets["PCIE1_PERST_N"]
    U15[64] += nets["PCIE1_CLKREQ_N"]
    U15[54] += nets["PCIE1_WAKE_N"]

    # MDI pairs to RJ45 #3
    U15[1] += nets["ETH2_MDI0_P"];   U15[2] += nets["ETH2_MDI0_N"]
    U15[4] += nets["ETH2_MDI1_P"];   U15[5] += nets["ETH2_MDI1_N"]
    U15[7] += nets["ETH2_MDI2_P"];   U15[8] += nets["ETH2_MDI2_N"]
    U15[10] += nets["ETH2_MDI3_P"];  U15[11] += nets["ETH2_MDI3_N"]

    # 25 MHz crystal (separate from U2's)
    Y2 = Part("Device", "Crystal", value="25MHz TCXO", ref="Y2",
              footprint="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm")
    U15[15] += Y2[1]; U15[16] += Y2[2]

    # LEDs
    U15[20] += nets["ETH2_LED_ACT"]
    U15[21] += nets["ETH2_LED_LINK"]

    # Power
    for p in [22, 30, 40, 50]:  U15[p] += V3P3
    for p in [23, 31, 41, 51]:  U15[p] += V3P3
    for p in [3, 6, 9, 12, 14, 17, 24, 29, 32, 39, 42, 49, 52, 60]:
        U15[p] += GND

    # Decoupling
    for i in range(6):
        c = C(value="100nF", ref=f"C_RTL2_{i+1}")
        c[1] += V3P3; c[2] += GND
    c_bulk = Part("Device", "C", value="10uF", ref="C_RTL2_BULK",
                  footprint="Capacitor_SMD:C_0603_1608Metric")
    c_bulk[1] += V3P3; c_bulk[2] += GND

    # RJ45 #3
    J21 = Part("Connector", "RJ45", value="RJ45-2.5G-#3", ref="J21",
               footprint="Connector_RJ:RJ45_Amphenol_RJHSE538X-02")
    J21[1] += nets["ETH2_MDI0_P"]; J21[2] += nets["ETH2_MDI0_N"]
    J21[3] += nets["ETH2_MDI1_P"]; J21[6] += nets["ETH2_MDI1_N"]
    J21[4] += nets["ETH2_MDI2_P"]; J21[5] += nets["ETH2_MDI2_N"]
    J21[7] += nets["ETH2_MDI3_P"]; J21[8] += nets["ETH2_MDI3_N"]

    # Bob-Smith on RJ45 #3
    chassis_gnd = Net("CHASSIS_GND")
    common = Net("BOBSMITH_J21")
    for pin in range(1, 9):
        r = R(value="75", ref=f"R_BS_J21_{pin}")
        r[1] += J21[pin]; r[2] += common
    c_bs = Part("Device", "C", value="1nF/2kV",
                ref="C_BS_J21",
                footprint="Capacitor_SMD:C_1210_3225Metric")
    c_bs[1] += common; c_bs[2] += chassis_gnd

    return U15, J21
