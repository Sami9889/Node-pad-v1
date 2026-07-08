"""
NodePad — PoE+ Power Delivery (optional, DNP by default)

  * U6: MP8007 PoE+ PD interface (802.3at, 25W)
  * T1: Flyback transformer (750317847 or equivalent)
  * Standard PoE PD front-end: bridge, TVS, PD signature resistor,
    classification resistor, isolation transformer.

Populate this section only if you need PoE input.  All parts have
"DNP" (Do Not Populate) in their value string so JLCPCB assembly skips
them when the "empty PoE" build is selected.

REVIEW BEFORE FAB:
  - PoE side needs >= 4mm creepage/clearance from carrier ground
  - Isolation transformer must be 1500 V rated per IEEE 802.3at
  - Classification resistor R_CLASS sets requested class (25W = class 4)
  - Verify MP8007 pin mapping against MPS datasheet
"""

import os
os.environ.setdefault("KICAD_SYMBOL_DIR", "/opt/kicad-libs/symbols")
os.environ.setdefault("KICAD9_SYMBOL_DIR", "/opt/kicad-libs/symbols")

from skidl import Part, Net, TEMPLATE, set_default_tool, KICAD9

set_default_tool(KICAD9)

R = Part("Device", "R", dest=TEMPLATE, footprint="Resistor_SMD:R_0402_1005Metric")
C = Part("Device", "C", dest=TEMPLATE, footprint="Capacitor_SMD:C_0402_1005Metric")


def build(nets):
    """Optional PoE+ front-end.  All parts DNP by default."""

    GND = nets["GND"]
    VIN_12V = nets["VIN_12V"]

    # Isolated PoE-side ground (chassis GND from RJ45 shield/BobSmith)
    PoE_GND = Net("PoE_GND")

    # ----- Center taps from RJ45 magnetics deliver PoE voltage ----------
    # PoE injects ~48V DC across pins 1-2 vs 3-6 (mode A) or 4-5 vs 7-8 (mode B)
    # The center taps of the RJ45 magnetics carry the DC. We tie ETH0_CT_A/B
    # (already defined in ethernet.py) into the PoE bridge.
    CT_A = Net("ETH0_CT_A")  # placeholder - would come from mag jack center tap
    CT_B = Net("ETH0_CT_B")

    # ----- Bridge rectifier (accepts either polarity of PoE) -----------
    # 4x diodes in a bridge, e.g. HD01-T (SMB, 1A, 100V)
    def diode(ref, dnp=True):
        d = Part("Device", "D",
                 value="HD01-T DNP" if dnp else "HD01-T",
                 ref=ref,
                 footprint="Diode_SMD:D_SMB")
        return d

    D1 = diode("D_POE_1"); D2 = diode("D_POE_2")
    D3 = diode("D_POE_3"); D4 = diode("D_POE_4")

    POE_VIN_POS = Net("POE_VIN_POS")   # ~48V after bridge
    POE_VIN_NEG = PoE_GND

    D1[1] += CT_A; D1[2] += POE_VIN_POS
    D2[1] += CT_B; D2[2] += POE_VIN_POS
    D3[1] += POE_VIN_NEG; D3[2] += CT_A
    D4[1] += POE_VIN_NEG; D4[2] += CT_B

    # ----- TVS on PoE input (SMBJ58A, 58V standoff, 92V clamp) ---------
    tvs = Part("Device", "D_TVS", value="SMBJ58A DNP",
               ref="D_POE_TVS",
               footprint="Diode_SMD:D_SMB")
    tvs[1] += POE_VIN_POS; tvs[2] += POE_VIN_NEG

    # ----- Bulk input capacitor (100nF/100V ceramic + 22uF/100V bulk) ---
    c_hf = Part("Device", "C", value="100nF/100V DNP",
                ref="C_POE_HF",
                footprint="Capacitor_SMD:C_1206_3216Metric")
    c_hf[1] += POE_VIN_POS; c_hf[2] += POE_VIN_NEG
    c_bulk = Part("Device", "C", value="22uF/100V DNP",
                  ref="C_POE_BULK",
                  footprint="Capacitor_SMD:C_1210_3225Metric")
    c_bulk[1] += POE_VIN_POS; c_bulk[2] += POE_VIN_NEG

    # ----- PD signature resistor (25 kΩ per 802.3at) --------------------
    R_SIG = R(value="25k DNP", ref="R_POE_SIG")
    R_SIG[1] += POE_VIN_POS; R_SIG[2] += POE_VIN_NEG

    # ----- Classification resistor (12.5 Ω for class 4 / 25W) ----------
    R_CLASS = R(value="12.5 DNP", ref="R_POE_CLASS")

    # ----- MP8007 PoE-PD interface + flyback (SOIC-16) ------------------
    U6 = Part("Connector_Generic", "Conn_01x16",
              value="MP8007 DNP",
              ref="U6",
              footprint="Package_SO:SOIC-16_3.9x9.9mm_P1.27mm")
    # TODO_VERIFY: MP8007 pin numbers from MPS datasheet
    U6[1]  += POE_VIN_POS         # VIN
    U6[2]  += POE_VIN_NEG         # GND
    U6[3]  += R_CLASS[1]          # RCLASS
    U6[4]  += POE_VIN_NEG         # RCLASS return
    R_CLASS[2] += POE_VIN_NEG
    U6[5]  += Net("PoE_SW")       # switch node -> transformer primary
    U6[6]  += Net("PoE_CS")       # current sense
    U6[7]  += Net("PoE_COMP")     # compensation
    U6[8]  += Net("PoE_FB")       # feedback
    U6[16] += POE_VIN_NEG         # exposed pad / GND

    # ----- Flyback transformer (isolated 48V -> 12V @ 2A) ---------------
    T1 = Part("Device", "Transformer_1P_SS",
              value="750317847 DNP",
              ref="T1",
              footprint="Package_DIP:DIP-8_W7.62mm")
    T1[1] += POE_VIN_POS
    T1[2] += Net("PoE_SW")
    T1[3] += Net("PoE_SEC_HI")
    T1[5] += GND               # isolated: connects to system GND after rectifier
    # (real transformer symbol has 4 winding pins; use best-effort)

    # ----- Secondary rectifier + filter --------------------------------
    D_sec = Part("Device", "D_Schottky",
                 value="SS36 DNP",
                 ref="D_POE_SEC",
                 footprint="Diode_SMD:D_SMB")
    D_sec[1] += Net("PoE_SEC_HI"); D_sec[2] += Net("PoE_SEC_RECT")

    c_sec = Part("Device", "C", value="47uF/25V DNP",
                 ref="C_POE_SEC",
                 footprint="Capacitor_SMD:C_1210_3225Metric")
    c_sec[1] += Net("PoE_SEC_RECT"); c_sec[2] += GND

    # ----- OR-ing diode to VIN_12V (so USB-C and PoE can coexist) -------
    D_or = Part("Device", "D_Schottky",
                value="SS36 DNP",
                ref="D_POE_OR",
                footprint="Diode_SMD:D_SMB")
    D_or[1] += Net("PoE_SEC_RECT"); D_or[2] += VIN_12V

    return U6, T1
