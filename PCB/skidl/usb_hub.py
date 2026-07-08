"""
NodePad — USB 3.0 hub + 4x USB-A downstream

  * U10: GL3523 USB 3.0 4-port hub (QFN-88 placeholder)
  * J8-J11: USB 3.0 Type-A receptacles
  * Simple TVS + ferrite per downstream VBUS

Note: TPS2553 power switches are drawn as generic 6-pin placeholders because
the KiCad std lib doesn't ship a TPS2553 symbol.  Swap for the real symbol
in KiCad's schematic editor after netlist import.

REVIEW BEFORE FAB:
  - GL3523 strap resistors for SS/HS enable
  - Current-limit resistor to GND on each TPS2553 (~30k for 1.2A limit)
"""

import os
os.environ.setdefault("KICAD_SYMBOL_DIR", "/opt/kicad-libs/symbols")
os.environ.setdefault("KICAD9_SYMBOL_DIR", "/opt/kicad-libs/symbols")

from skidl import Part, Net, TEMPLATE, set_default_tool, KICAD9

set_default_tool(KICAD9)

R = Part("Device", "R", dest=TEMPLATE, footprint="Resistor_SMD:R_0402_1005Metric")
C = Part("Device", "C", dest=TEMPLATE, footprint="Capacitor_SMD:C_0402_1005Metric")


def _c(J, n, net):
    """Connect integer pin 1..88 on a Conn_02x44_Row_Letter_Last symbol."""
    key = f"{n}a" if n <= 44 else f"{n-44}b"
    J[key] += net


def build_usb3_port(ref_j, ref_switch, V5, GND, stx_p, stx_n, srx_p, srx_n,
                    hs_dp, hs_dm, oc_flag):
    """USB3 Type-A vertical jack + TPS2553 placeholder + TVS."""

    J = Part("Connector", "USB3_A", value="USB3-A", ref=ref_j,
             footprint="Connector_USB:USB3_A_Molex_48393-0002_Horizontal")
    vbus = Net(f"VBUS_{ref_j}")
    J["VBUS"] += vbus
    J["GND"]  += GND
    J["D+"]   += hs_dp
    J["D-"]   += hs_dm
    J["SSRX+"] += srx_p
    J["SSRX-"] += srx_n
    J["SSTX+"] += stx_p
    J["SSTX-"] += stx_n
    J["SHIELD"] += GND

    # TPS2553 placeholder (6-pin: 1=EN 2=GND 3=IN 4=OUT 5=FAULT 6=ILIM)
    SW = Part("Connector_Generic", "Conn_01x06",
              value="TPS2553",
              ref=ref_switch,
              footprint="Package_TO_SOT_SMD:SOT-23-6")
    SW[1] += V5             # EN
    SW[2] += GND
    SW[3] += V5             # IN
    SW[4] += vbus           # OUT
    SW[5] += oc_flag        # FAULT
    R_lim = R(value="30k", ref=f"R_ILIM_{ref_j}")
    SW[6] += R_lim[1]; R_lim[2] += GND

    # Bulk cap + TVS on VBUS
    c_out = Part("Device", "C", value="150uF/6.3V", ref=f"C_VB_{ref_j}",
                 footprint="Capacitor_SMD:C_1206_3216Metric")
    c_out[1] += vbus; c_out[2] += GND
    tvs = Part("Device", "D_TVS", value="SMBJ5.0A", ref=f"D_TVS_{ref_j}",
               footprint="Diode_SMD:D_SMB")
    tvs[1] += vbus; tvs[2] += GND


def build(nets):
    V5   = nets["+5V"]
    V3P3 = nets["+3V3_AUX"]
    GND  = nets["GND"]

    # U10: GL3523 (placeholder Conn_02x44_Row_Letter_Last = 88 pins)
    U10 = Part("Connector_Generic", "Conn_02x44_Row_Letter_Last",
               value="GL3523",
               ref="U10",
               footprint="Package_DFN_QFN:QFN-88_10x10mm_P0.4mm")

    # Upstream port  TODO_VERIFY
    _c(U10, 1, nets["USB3_TX_P"]);  _c(U10, 2, nets["USB3_TX_N"])
    _c(U10, 4, nets["USB3_RX_P"]);  _c(U10, 5, nets["USB3_RX_N"])
    _c(U10, 7, nets["USB3_DP"]);    _c(U10, 8, nets["USB3_DM"])

    # 4 downstream ports
    ss_map = [(10,11,13,14), (16,17,19,20), (22,23,25,26), (28,29,31,32)]
    hs_map = [(34,35), (37,38), (40,41), (43,44)]
    oc_map = [50, 51, 52, 53]

    for i in range(4):
        stx_p_pin, stx_n_pin, srx_p_pin, srx_n_pin = ss_map[i]
        hdp_pin, hdm_pin = hs_map[i]

        tx_p = Net(f"HUB_P{i+1}_TX_P"); tx_n = Net(f"HUB_P{i+1}_TX_N")
        rx_p = Net(f"HUB_P{i+1}_RX_P"); rx_n = Net(f"HUB_P{i+1}_RX_N")
        dp   = Net(f"HUB_P{i+1}_DP");   dm   = Net(f"HUB_P{i+1}_DM")
        oc   = Net(f"HUB_P{i+1}_OC_N")

        _c(U10, stx_p_pin, tx_p); _c(U10, stx_n_pin, tx_n)
        _c(U10, srx_p_pin, rx_p); _c(U10, srx_n_pin, rx_n)
        _c(U10, hdp_pin, dp);     _c(U10, hdm_pin, dm)
        _c(U10, oc_map[i], oc)

        build_usb3_port(f"J{8+i}", f"U{11+i}", V5, GND,
                        stx_p=rx_p, stx_n=rx_n,   # hub->device
                        srx_p=tx_p, srx_n=tx_n,   # device->hub
                        hs_dp=dp, hs_dm=dm, oc_flag=oc)

    # Power / GND on GL3523
    for p in [60, 65, 70, 75]:  _c(U10, p, V3P3)
    for p in [15, 21, 27, 33, 45, 54, 61, 66, 71, 76]:  _c(U10, p, GND)

    # 25 MHz crystal (2-pin)
    Y_HUB = Part("Device", "Crystal", value="25MHz", ref="Y_HUB",
                 footprint="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm")
    _c(U10, 46, Y_HUB[1]); _c(U10, 47, Y_HUB[2])

    # Reset + strap
    R_rst = R(value="10k", ref="R_HUB_RST")
    R_rst[1] += V3P3
    _c(U10, 48, R_rst[2])

    R_bp = R(value="10k", ref="R_HUB_BP")
    R_bp[1] += V3P3
    _c(U10, 49, R_bp[2])

    # LDO output cap
    LDO_INT = Net("HUB_VDD11_INT")
    _c(U10, 80, LDO_INT); _c(U10, 82, LDO_INT)
    c_ldo = Part("Device", "C", value="4.7uF", ref="C_HUB_LDO",
                 footprint="Capacitor_SMD:C_0603_1608Metric")
    c_ldo[1] += LDO_INT; c_ldo[2] += GND

    # Decoupling
    for i in range(8):
        c = C(value="100nF", ref=f"C_HUB_{i+1}")
        c[1] += V3P3; c[2] += GND
    c_bulk = Part("Device", "C", value="10uF", ref="C_HUB_BULK",
                  footprint="Capacitor_SMD:C_0603_1608Metric")
    c_bulk[1] += V3P3; c_bulk[2] += GND

    return U10
