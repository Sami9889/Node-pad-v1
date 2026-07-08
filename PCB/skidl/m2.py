"""
NodePad — M.2 slots

  * J5: M.2 M-key 2280 socket -> NVMe SSD storage, PCIe x1 Gen 2 from CM5 Combo0
  * J6: M.2 E-key 2230 socket -> WiFi/BT card,   PCIe x1 Gen 2 from CM5 Combo1
                                  (or use for 2nd 2.5GbE NIC via M.2 card)

Both slots powered from 3.3V @ up to 3A.  Dedicated bulk decoupling
on each slot's 3.3V pin.
"""

import os
os.environ.setdefault("KICAD_SYMBOL_DIR", "/opt/kicad-libs/symbols")
os.environ.setdefault("KICAD9_SYMBOL_DIR", "/opt/kicad-libs/symbols")

from skidl import Part, Net, TEMPLATE, set_default_tool, KICAD9

set_default_tool(KICAD9)

R = Part("Device", "R", dest=TEMPLATE, footprint="Resistor_SMD:R_0402_1005Metric")
C = Part("Device", "C", dest=TEMPLATE, footprint="Capacitor_SMD:C_0402_1005Metric")


def build(nets):
    _NC = Net("__NC__")

    V3P3 = nets["+3V3_AUX"]
    V5   = nets["+5V"]
    GND  = nets["GND"]

    # ------------------------------------------------------------------
    # J5 : M.2 M-key 2280 - NVMe SSD
    # 75-pin edge connector; here modeled with generic Conn placeholder.
    # Pinout follows PCIe M-key spec (JEDEC MO-297).
    # ------------------------------------------------------------------
    J5 = Part("Connector_Generic", "Conn_02x38_Odd_Even",
              value="M.2 M-key 2280",
              ref="J5",
              footprint="Connector_Card:M.2_M-Key_Socket_Vertical")

    # Reference pin assignments (M-key subset)
    # TODO_VERIFY every pin below against JEDEC MO-297 M-key spec
    # Power pins (multiple 3.3V, GND)
    for p in [69, 71, 73, 75]:   # +3V3
        J5[p] += V3P3
    for p in [70, 72, 74]:       # GND
        J5[p] += GND

    # PCIe lane 0 (only lane used for x1 NVMe)
    J5[35] += nets["PCIE0_TX_P"];   J5[33] += nets["PCIE0_TX_N"]
    J5[29] += nets["PCIE0_RX_P"];   J5[31] += nets["PCIE0_RX_N"]
    J5[27] += nets["PCIE0_REFCLK_P"]; J5[25] += nets["PCIE0_REFCLK_N"]
    J5[50] += nets["PCIE0_PERST_N"]
    J5[52] += nets["PCIE0_CLKREQ_N"]
    J5[54] += nets["PCIE0_WAKE_N"]

    # Activity LED output (open-drain, drives D5)
    J5[11] += nets["NVME_ACT_N"]

    # Pull-ups on control signals
    R_perst = R(value="10k", ref="R_M2M_PERST"); R_perst[1] += V3P3; R_perst[2] += nets["PCIE0_PERST_N"]

    # SATA differential (M-key also supports SATA; unused - handled by NC loop below)

    # Reserved / unused pins
    # Assign NC where practical (avoid ERC noise on ~40 unused pins)
    for p in range(1, 76):
        try:
            if not J5[p].is_connected():
                J5[p] += _NC
        except Exception:
            pass

    # Bulk decoupling on 3.3V rail near J5
    c_bulk = Part("Device", "C", value="22uF/6.3V",
                  ref="C_M2M_BULK",
                  footprint="Capacitor_SMD:C_0805_2012Metric")
    c_bulk[1] += V3P3; c_bulk[2] += GND
    for i in range(4):
        c = C(value="100nF", ref=f"C_M2M_{i+1}")
        c[1] += V3P3; c[2] += GND

    # ------------------------------------------------------------------
    # J6 : M.2 E-key 2230 - WiFi/BT or 2nd NIC
    # ------------------------------------------------------------------
    J6 = Part("Connector_Generic", "Conn_02x38_Odd_Even",
              value="M.2 E-key 2230",
              ref="J6",
              footprint="Connector_Card:M.2_E-Key_Socket_Vertical")

    # Power
    for p in [2, 4, 72, 74]:
        J6[p] += V3P3
    for p in [1, 7, 9, 11, 15, 17, 19, 25, 33, 39, 45, 51, 57, 63, 69, 75]:
        J6[p] += GND

    # PCIe (E-key uses PCIe0/1 on pins 21-51)
    # TODO_VERIFY: E-key pin layout differs from M-key
    J6[21] += Net("E_PCIE_TX_P");  J6[23] += Net("E_PCIE_TX_N")
    J6[29] += Net("E_PCIE_RX_P");  J6[31] += Net("E_PCIE_RX_N")
    J6[41] += Net("E_PCIE_REFCLK_P"); J6[43] += Net("E_PCIE_REFCLK_N")

    # If populated with 2nd NIC, remap E_PCIE_* to PCIE1_*.
    # For default (WiFi/BT) build, use dedicated Combo lane.
    # Here we use the existing PCIE1_ lane but net-tie via 0-ohm option resistors.
    R_opt1 = R(value="0/DNP", ref="R_E_OPT_1"); R_opt1[1] += Net("E_PCIE_TX_P"); R_opt1[2] += nets["PCIE1_TX_P"]
    R_opt2 = R(value="0/DNP", ref="R_E_OPT_2"); R_opt2[1] += Net("E_PCIE_TX_N"); R_opt2[2] += nets["PCIE1_TX_N"]
    R_opt3 = R(value="0/DNP", ref="R_E_OPT_3"); R_opt3[1] += Net("E_PCIE_RX_P"); R_opt3[2] += nets["PCIE1_RX_P"]
    R_opt4 = R(value="0/DNP", ref="R_E_OPT_4"); R_opt4[1] += Net("E_PCIE_RX_N"); R_opt4[2] += nets["PCIE1_RX_N"]

    # USB 2.0 (for WiFi combo cards that use USB for BT)
    J6[36] += nets["USB2_1_DP"];  J6[38] += nets["USB2_1_DM"]

    # CLK_REQ, W_DISABLE, LED
    J6[50] += nets["PCIE1_CLKREQ_N"]
    J6[56] += nets["PCIE1_PERST_N"]
    J6[46] += Net("WIFI_DISABLE1_N")
    J6[48] += Net("WIFI_DISABLE2_N")

    # NC the rest
    for p in range(1, 76):
        try:
            if not J6[p].is_connected():
                J6[p] += _NC
        except Exception:
            pass

    # Bulk decoupling
    c_bulk2 = Part("Device", "C", value="10uF",
                   ref="C_M2E_BULK",
                   footprint="Capacitor_SMD:C_0603_1608Metric")
    c_bulk2[1] += V3P3; c_bulk2[2] += GND
    for i in range(3):
        c = C(value="100nF", ref=f"C_M2E_{i+1}")
        c[1] += V3P3; c[2] += GND

    return J5, J6
