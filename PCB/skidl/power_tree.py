"""
NodePad — Power Tree (SKiDL definition)

Generates the KiCad netlist for the power subsystem:

  USB-C VBUS ──► CH224K (PD sink, 12V request) ──► VIN_12V
                                                    │
                                                    ├──► MP2315 buck ──► +5V @ 3A
                                                    │                     │
                                                    │                     └──► AP2112 LDO ──► +3V3_AUX @ 600mA
                                                    │
                                                    └──► (optional PoE PD input path; not populated here)

Run:
    KICAD_SYMBOL_DIR=/opt/kicad-libs/symbols \\
    python3 power_tree.py

Outputs:
    ./netlists/power_tree.net   (KiCad netlist)

License: CERN-OHL-P v2
Author:  Samrath "Sami" Singh
"""

import os
os.environ.setdefault("KICAD_SYMBOL_DIR", "/opt/kicad-libs/symbols")
os.environ.setdefault("KICAD9_SYMBOL_DIR", "/opt/kicad-libs/symbols")

from skidl import (
    Part, Net, TEMPLATE, generate_netlist, set_default_tool, KICAD9,
    ERC, no_files
)

set_default_tool(KICAD9)


# ---------------------------------------------------------------------------
# Reusable passive templates
# ---------------------------------------------------------------------------
R = Part("Device", "R", dest=TEMPLATE, footprint="Resistor_SMD:R_0402_1005Metric")
C = Part("Device", "C", dest=TEMPLATE, footprint="Capacitor_SMD:C_0402_1005Metric")
C_bulk = Part("Device", "C", dest=TEMPLATE, footprint="Capacitor_SMD:C_0805_2012Metric")
L = Part("Device", "L", dest=TEMPLATE, footprint="Inductor_SMD:L_0805_2012Metric")


# ---------------------------------------------------------------------------
# Nets
# ---------------------------------------------------------------------------
GND      = Net("GND");      GND.drive     = 3
VBUS_USB = Net("VBUS_USB")            # raw 5V from USB-C, before PD
VIN_12V  = Net("VIN_12V")             # main input rail after PD negotiation (5-20V)
V5       = Net("+5V")                 # main 5V rail out of MP2315 buck
V3P3     = Net("+3V3_AUX")            # 3.3V aux for RTC, LEDs, glue logic
CC1      = Net("USB_CC1")
CC2      = Net("USB_CC2")
DP       = Net("USB_DP")              # USB 2.0 D+ (for OTG)
DM       = Net("USB_DM")              # USB 2.0 D-
USB_ID   = Net("USB_ID")              # for future OTG detect (optional)


# ---------------------------------------------------------------------------
# J7 : USB-C receptacle (16-pin, GCT USB4105 style)
# LCSC C165948
# ---------------------------------------------------------------------------
# Using generic Connector symbol; footprint will be USB_C_Receptacle_HRO_TYPE-C-31-M-12
J7 = Part("Connector", "USB_C_Receptacle_USB2.0_16P",
          value="USB-C",
          ref="J7",
          footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12")

# Power pins (A4, A9, B4, B9)
J7["VBUS"] += VBUS_USB
# Ground pins (A1, A12, B1, B12, shield)
J7["GND"]  += GND
J7["SHIELD"] += GND
# CC (A5, B5)
J7["CC1"] += CC1
J7["CC2"] += CC2
# USB 2.0 data (A6, A7, B6, B7)
J7["D+"] += DP
J7["D-"] += DM
J7["SBU1"] += Net("USB_SBU1")   # unused for now
J7["SBU2"] += Net("USB_SBU2")   # unused for now


# ---------------------------------------------------------------------------
# U5 : CH224K USB-C PD sink (programmable trigger)
# LCSC C970725
#
# CFG1/CFG2/CFG3 resistor combination selects requested voltage.
# For 12V request:  CFG1=open  CFG2=open  CFG3=short-to-GND  (per datasheet Table 3)
# Output on VBUS pin drives VIN_12V rail once PD contract is negotiated.
# ---------------------------------------------------------------------------
U5 = Part("Connector_Generic", "Conn_01x10",  # placeholder; real symbol added in Rev 2
          value="CH224K",
          ref="U5",
          footprint="Package_SO:ESSOP-10_3x3mm_P0.5mm")
# For the placeholder we treat pin 1..10 as CH224K pinout:
#   1  VBUS_IN     (from USB-C VBUS after ESD)
#   2  VBUS_OUT    (regulated VIN_12V)
#   3  CC1
#   4  CC2
#   5  CFG1
#   6  CFG2
#   7  CFG3
#   8  GND
#   9  DP passthrough (optional)
#  10  DM passthrough (optional)
U5[1] += VBUS_USB
U5[2] += VIN_12V
U5[3] += CC1
U5[4] += CC2

# CFG resistor network for 12V request
R_cfg1 = R(value="10k", ref="R1")     # CFG1 -> GND  (open in some configs)
R_cfg2 = R(value="10k", ref="R2")     # CFG2 -> GND
R_cfg3_gnd = R(value="0", ref="R3")   # CFG3 short to GND  => 12V request per datasheet
U5[5] += R_cfg1[1];  R_cfg1[2] += GND       # (populate/DNP as needed for other voltages)
U5[6] += R_cfg2[1];  R_cfg2[2] += GND
U5[7] += R_cfg3_gnd[1]; R_cfg3_gnd[2] += GND

U5[8] += GND
U5[9] += DP     # pass-through
U5[10] += DM

# Input decoupling on CH224K VBUS_IN
C_in_pd = C(value="1uF", ref="C1"); C_in_pd[1] += VBUS_USB; C_in_pd[2] += GND
C_out_pd = C(value="1uF", ref="C2"); C_out_pd[1] += VIN_12V; C_out_pd[2] += GND

# TVS/ESD on VBUS (optional but strongly recommended)
D_esd_vbus = Part("Device", "D_TVS", value="SMBJ12A",
                  footprint="Diode_SMD:D_SMB")
D_esd_vbus.ref = "D6"
D_esd_vbus[1] += VBUS_USB
D_esd_vbus[2] += GND


# ---------------------------------------------------------------------------
# U3 : MP2315 step-down converter (VIN 4.5-24V, 3A, 500kHz fixed)
# LCSC C89358
# Configured for 5V output via feedback divider.
#
# FB target = 0.8V typ.
# 5V output => R_top / R_bot = (5 - 0.8) / 0.8 = 5.25
# Pick R_top = 52.5k, R_bot = 10k  =>  Vout ~= 5.00V
# ---------------------------------------------------------------------------
U3 = Part("Connector_Generic", "Conn_01x08",   # placeholder for MP2315 (SOT-563-8)
          value="MP2315",
          ref="U3",
          footprint="Package_SO:SOT-563_1.6x1.6mm_P0.5mm")
# MP2315 pinout:
#   1  BST      (bootstrap cap to SW)
#   2  IN       (VIN)
#   3  SW       (switch node -> inductor)
#   4  GND
#   5  FB       (feedback)
#   6  EN       (enable, pull up to VIN)
#   7  COMP     (loop compensation)
#   8  GND (EP)

SW_NODE = Net("SW_5V")   # internal switch node - keep short and shielded on PCB

# Inputs
U3[2] += VIN_12V
C_in_buck = C_bulk(value="22uF/25V", ref="C3")
C_in_buck[1] += VIN_12V; C_in_buck[2] += GND

# Enable (pulled up to VIN through 100k for auto-start)
R_en = R(value="100k", ref="R4")
R_en[1] += VIN_12V; R_en[2] += U3[6]

# Switch node + inductor + bootstrap
L1 = L(value="4.7uH/3A", ref="L1",
       footprint="Inductor_SMD:L_Bourns_SRP1265A")
U3[3] += SW_NODE
L1[1]  += SW_NODE
L1[2]  += V5

# Bootstrap cap (BST -> SW node)
C_bst = C(value="100nF", ref="C4")
C_bst[1] += U3[1]; C_bst[2] += SW_NODE

# GND
U3[4] += GND
U3[8] += GND

# Feedback divider (0.8V ref, 5V out)
R_fb_top = R(value="52.3k", ref="R5")  # closest E96
R_fb_bot = R(value="10k",  ref="R6")
R_fb_top[1] += V5;     R_fb_top[2] += U3[5]
R_fb_bot[1] += U3[5];  R_fb_bot[2] += GND

# COMP network (typical for MP2315 at 500kHz with 22uF output)
R_comp = R(value="10k", ref="R7")
C_comp = C(value="2.2nF", ref="C5")
C_comp2 = C(value="100pF", ref="C6")
U3[7] += R_comp[1]
R_comp[2] += C_comp[1]; C_comp[2] += GND
U3[7] += C_comp2[1]; C_comp2[2] += GND

# Output caps
for i, v in enumerate(["22uF/25V", "22uF/25V", "10uF/16V", "100nF"]):
    fp = C_bulk if "22uF" in v else C
    c = fp(value=v, ref=f"C{10+i}")
    c[1] += V5; c[2] += GND


# ---------------------------------------------------------------------------
# U4 : AP2112K-3.3 LDO  (600mA, low-Iq, 3.3V fixed)
# LCSC C51118
#
# SOT-23-5:  1=VIN  2=GND  3=EN  4=NC  5=VOUT
# ---------------------------------------------------------------------------
U4 = Part("Regulator_Linear", "AP2112K-3.3",
          value="AP2112K-3.3",
          ref="U4",
          footprint="Package_TO_SOT_SMD:SOT-23-5")
U4["VIN"] += V5
U4["GND"] += GND
U4["EN"]  += V5      # always-on: tie EN to VIN
U4["VOUT"]+= V3P3

C_ldo_in  = C(value="1uF", ref="C15"); C_ldo_in[1]  += V5;   C_ldo_in[2]  += GND
C_ldo_out = C(value="1uF", ref="C16"); C_ldo_out[1] += V3P3; C_ldo_out[2] += GND


# ---------------------------------------------------------------------------
# Test points (assembly + debug)
# ---------------------------------------------------------------------------
def add_test_point(net, ref):
    tp = Part("Connector", "TestPoint", value="TP",
              ref=ref,
              footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp[1] += net

add_test_point(VBUS_USB, "TP1")
add_test_point(VIN_12V,  "TP2")
add_test_point(V5,       "TP3")
add_test_point(V3P3,     "TP4")
add_test_point(GND,      "TP5")


# ---------------------------------------------------------------------------
# ERC + Netlist
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    os.makedirs("netlists", exist_ok=True)
    ERC()
    generate_netlist(file_="netlists/power_tree.net")
    print("[OK] Netlist written -> netlists/power_tree.net")
