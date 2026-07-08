"""
NodePad — Missing-parts pass (added during verification).

Small things that should have been in the original blocks but weren't:

  * Boot-select pull-ups (10k) so CM5 boots from eMMC by default
  * Reset button debouncing cap (100nF)
  * VIN_12V bulk cap
  * Power-EN RC filter (delayed startup)
  * PCIe REFCLK termination option (0Ω DNP + 100Ω term)
  * NVMe activity LED pull-up
"""

import os
os.environ.setdefault("KICAD_SYMBOL_DIR", "/opt/kicad-libs/symbols")
os.environ.setdefault("KICAD9_SYMBOL_DIR", "/opt/kicad-libs/symbols")

from skidl import Part, Net, TEMPLATE, set_default_tool, KICAD9

set_default_tool(KICAD9)

R = Part("Device", "R", dest=TEMPLATE, footprint="Resistor_SMD:R_0402_1005Metric")
C = Part("Device", "C", dest=TEMPLATE, footprint="Capacitor_SMD:C_0402_1005Metric")


def build(nets):
    GND     = nets["GND"]
    V3P3    = nets["+3V3_AUX"]
    V5      = nets["+5V"]
    VIN_12V = nets["VIN_12V"]

    # ------------------------------------------------------------------
    # 1. Boot-select pull-ups (CM5 boots from eMMC when all three high)
    # ------------------------------------------------------------------
    for i, sig in enumerate(["CM5_BOOT0", "CM5_BOOT1", "CM5_BOOT2"]):
        r = R(value="10k", ref=f"R_BOOT{i}_PU")
        r[1] += V3P3; r[2] += nets[sig]

    # ------------------------------------------------------------------
    # 2. Reset button debouncing cap on CM5_RUN_N
    # ------------------------------------------------------------------
    c_debounce = C(value="100nF", ref="C_RESET_DB")
    c_debounce[1] += nets["CM5_RUN_N"]; c_debounce[2] += GND
    # Also a 10k pull-up so the button pulls DOWN cleanly
    r_reset_pu = R(value="10k", ref="R_RESET_PU")
    r_reset_pu[1] += V3P3; r_reset_pu[2] += nets["CM5_RUN_N"]

    # And on MASKROM button
    r_mask_pu = R(value="10k", ref="R_MASKROM_PU")
    r_mask_pu[1] += V3P3; r_mask_pu[2] += nets["CM5_MASKROM"]

    # ------------------------------------------------------------------
    # 3. VIN_12V bulk cap (electrolytic + ceramic on MP2315 input)
    # ------------------------------------------------------------------
    c_vin_bulk = Part("Device", "C", value="47uF/25V",
                      ref="C_VIN_BULK",
                      footprint="Capacitor_SMD:CP_Elec_5x5.4")
    c_vin_bulk[1] += VIN_12V; c_vin_bulk[2] += GND
    c_vin_hf = Part("Device", "C", value="100nF",
                    ref="C_VIN_HF",
                    footprint="Capacitor_SMD:C_0402_1005Metric")
    c_vin_hf[1] += VIN_12V; c_vin_hf[2] += GND

    # ------------------------------------------------------------------
    # 4. Power-EN RC filter (delays CM5_POWER_EN by ~50 ms after 5V rises)
    # ------------------------------------------------------------------
    r_pgood = R(value="100k", ref="R_PWR_EN_DLY")
    c_pgood = C(value="470nF", ref="C_PWR_EN_DLY")
    r_pgood[1] += V5;                r_pgood[2] += nets["CM5_POWER_EN"]
    c_pgood[1] += nets["CM5_POWER_EN"]; c_pgood[2] += GND

    # ------------------------------------------------------------------
    # 5. PCIe REFCLK termination (100Ω differential, DNP by default)
    # ------------------------------------------------------------------
    r_term_p = R(value="49.9 DNP", ref="R_PCIE0_TERM_P")
    r_term_p[1] += nets["PCIE0_REFCLK_P"]; r_term_p[2] += Net("PCIE0_TERM_MID")
    r_term_n = R(value="49.9 DNP", ref="R_PCIE0_TERM_N")
    r_term_n[1] += nets["PCIE0_REFCLK_N"]; r_term_n[2] += Net("PCIE0_TERM_MID")

    # ------------------------------------------------------------------
    # 6. NVMe activity LED pull-up (M.2 pin 11 is open-drain)
    # ------------------------------------------------------------------
    r_nvme_pu = R(value="10k", ref="R_NVME_ACT_PU")
    r_nvme_pu[1] += V3P3; r_nvme_pu[2] += nets["NVME_ACT_N"]

    # ------------------------------------------------------------------
    # 7. PCIe CLKREQ# / PERST# pull-ups (per PCIe spec)
    # ------------------------------------------------------------------
    for sig in ["PCIE0_CLKREQ_N", "PCIE0_PERST_N", "PCIE1_CLKREQ_N", "PCIE1_PERST_N"]:
        if sig in nets:
            r = R(value="10k", ref=f"R_PU_{sig[:-2]}")
            r[1] += V3P3; r[2] += nets[sig]

    # ------------------------------------------------------------------
    # 8. I2C1 pull-ups (I2C0 already handled in rtc.py)
    # ------------------------------------------------------------------
    r_i2c1_sda = R(value="4.7k", ref="R_I2C1_SDA_PU")
    r_i2c1_sda[1] += V3P3; r_i2c1_sda[2] += nets["I2C1_SDA"]
    r_i2c1_scl = R(value="4.7k", ref="R_I2C1_SCL_PU")
    r_i2c1_scl[1] += V3P3; r_i2c1_scl[2] += nets["I2C1_SCL"]

    # ------------------------------------------------------------------
    # 9. USB-C SBU pull-downs (per USB-C spec - prevents floating pins)
    # ------------------------------------------------------------------
    # SBU nets already exist inside power_tree.py's USB-C block
    # (nothing to do here — noted for the audit trail)
