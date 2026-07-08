"""
NodePad — Radxa CM5 SoM connectors (J1, J2)

Two 100-pin Hirose DF40C-100DS-0.4V receptacles.

CRITICAL: Every pin marked TODO_VERIFY MUST be checked against the official
Radxa CM5 datasheet before fab:
    https://docs.radxa.com/en/som/cm/cm5/hardware/hardware-interface

Rev-1 fab risk if this is wrong: dead board, no boot, no networking.
"""

import os
os.environ.setdefault("KICAD_SYMBOL_DIR", "/opt/kicad-libs/symbols")
os.environ.setdefault("KICAD9_SYMBOL_DIR", "/opt/kicad-libs/symbols")

from skidl import Part, Net, TEMPLATE, set_default_tool, KICAD9

set_default_tool(KICAD9)

C = Part("Device", "C", dest=TEMPLATE,
         footprint="Capacitor_SMD:C_0402_1005Metric")


def _c(J, n, net):
    """Connect integer pin 1..100 on a Conn_02x50_Row_Letter_Last symbol.
       Pins are labelled '1a'..'50a' (row A) and '1b'..'50b' (row B)."""
    key = f"{n}a" if n <= 50 else f"{n-50}b"
    J[key] += net


def _pin_ref(J, n):
    """Return the KiCad pin key string for integer 1..100."""
    return f"{n}a" if n <= 50 else f"{n-50}b"


def build(nets):
    _NC = Net("__NC__")
    J1 = Part("Connector_Generic", "Conn_02x50_Row_Letter_Last",
              value="CM5-J1", ref="J1",
              footprint="Connector_Hirose:Hirose_DF40C-100DS-0.4V_1x100-1MP_P0.40mm_Vertical")
    J2 = Part("Connector_Generic", "Conn_02x50_Row_Letter_Last",
              value="CM5-J2", ref="J2",
              footprint="Connector_Hirose:Hirose_DF40C-100DS-0.4V_1x100-1MP_P0.40mm_Vertical")

    GND  = nets["GND"]
    V5   = nets["+5V"]
    V3P3 = nets["+3V3_AUX"]

    # Power / ground pins
    for p in [1, 2, 3, 4, 5, 6]:                                _c(J1, p, V5)
    for p in [7, 15, 25, 35, 45, 55, 65, 75, 85, 95,
              10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:        _c(J1, p, GND)
    for p in [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:     _c(J2, p, GND)
    for p in [87, 88, 89]:                                      _c(J1, p, V3P3)

    # HDMI 2.0 output  TODO_VERIFY
    _c(J1, 11, nets["HDMI_TX2_P"]);   _c(J1, 12, nets["HDMI_TX2_N"])
    _c(J1, 13, nets["HDMI_TX1_P"]);   _c(J1, 14, nets["HDMI_TX1_N"])
    _c(J1, 16, nets["HDMI_TX0_P"]);   _c(J1, 17, nets["HDMI_TX0_N"])
    _c(J1, 18, nets["HDMI_CLK_P"]);   _c(J1, 19, nets["HDMI_CLK_N"])
    _c(J1, 21, nets["HDMI_CEC"])
    _c(J1, 22, nets["HDMI_HPD"])
    _c(J1, 23, nets["HDMI_DDC_SDA"])
    _c(J1, 24, nets["HDMI_DDC_SCL"])

    # USB 3.0 SS + companion USB 2.0  TODO_VERIFY
    _c(J1, 26, nets["USB3_TX_P"]);    _c(J1, 27, nets["USB3_TX_N"])
    _c(J1, 28, nets["USB3_RX_P"]);    _c(J1, 29, nets["USB3_RX_N"])
    _c(J1, 31, nets["USB3_DP"]);      _c(J1, 32, nets["USB3_DM"])

    # PCIe 2.1 Combo0 (M-key NVMe)  TODO_VERIFY
    _c(J1, 33, nets["PCIE0_TX_P"]);   _c(J1, 34, nets["PCIE0_TX_N"])
    _c(J1, 36, nets["PCIE0_RX_P"]);   _c(J1, 37, nets["PCIE0_RX_N"])
    _c(J1, 39, nets["PCIE0_REFCLK_P"]); _c(J1, 41, nets["PCIE0_REFCLK_N"])
    _c(J1, 42, nets["PCIE0_PERST_N"])
    _c(J1, 43, nets["PCIE0_CLKREQ_N"])
    _c(J1, 44, nets["PCIE0_WAKE_N"])

    # Native GbE MDI to RJ45 #1  TODO_VERIFY
    _c(J1, 46, nets["ETH0_MDI0_P"]);  _c(J1, 47, nets["ETH0_MDI0_N"])
    _c(J1, 48, nets["ETH0_MDI1_P"]);  _c(J1, 49, nets["ETH0_MDI1_N"])
    _c(J1, 51, nets["ETH0_MDI2_P"]);  _c(J1, 52, nets["ETH0_MDI2_N"])
    _c(J1, 53, nets["ETH0_MDI3_P"]);  _c(J1, 54, nets["ETH0_MDI3_N"])
    _c(J1, 56, nets["ETH0_LED_ACT"])
    _c(J1, 57, nets["ETH0_LED_LINK"])

    # USB 2.0 spare hosts + OTG
    _c(J1, 58, nets["USB2_1_DP"]);    _c(J1, 59, nets["USB2_1_DM"])
    _c(J1, 61, nets["USB2_2_DP"]);    _c(J1, 62, nets["USB2_2_DM"])
    _c(J1, 63, nets["USB_DP"]);       _c(J1, 64, nets["USB_DM"])

    # Reset / boot / power good
    _c(J1, 66, nets["CM5_RUN_N"])
    _c(J1, 67, nets["CM5_MASKROM"])
    _c(J1, 68, nets["CM5_POWER_EN"])
    _c(J1, 69, nets["CM5_PWR_GOOD"])
    _c(J1, 71, nets["CM5_BOOT0"])
    _c(J1, 72, nets["CM5_BOOT1"])
    _c(J1, 73, nets["CM5_BOOT2"])

    # microSD
    _c(J1, 76, nets["SD_CLK"])
    _c(J1, 77, nets["SD_CMD"])
    _c(J1, 78, nets["SD_D0"])
    _c(J1, 79, nets["SD_D1"])
    _c(J1, 81, nets["SD_D2"])
    _c(J1, 82, nets["SD_D3"])
    _c(J1, 83, nets["SD_DET_N"])

    # J2: PCIe1, I2C, SPI, UART, PWM, GPIO breakout
    _c(J2, 2, nets["PCIE1_TX_P"]);   _c(J2, 3, nets["PCIE1_TX_N"])
    _c(J2, 4, nets["PCIE1_RX_P"]);   _c(J2, 5, nets["PCIE1_RX_N"])
    _c(J2, 7, nets["PCIE1_REFCLK_P"]); _c(J2, 8, nets["PCIE1_REFCLK_N"])
    _c(J2, 9, nets["PCIE1_PERST_N"])
    _c(J2, 11, nets["PCIE1_CLKREQ_N"])
    _c(J2, 12, nets["PCIE1_WAKE_N"])
    _c(J2, 14, nets["I2C0_SDA"])
    _c(J2, 15, nets["I2C0_SCL"])
    _c(J2, 17, nets["I2C1_SDA"])
    _c(J2, 18, nets["I2C1_SCL"])
    _c(J2, 21, nets["UART0_TX"])
    _c(J2, 22, nets["UART0_RX"])
    _c(J2, 24, nets["UART2_TX"])
    _c(J2, 25, nets["UART2_RX"])
    _c(J2, 27, nets["SPI0_MOSI"])
    _c(J2, 28, nets["SPI0_MISO"])
    _c(J2, 29, nets["SPI0_SCLK"])
    _c(J2, 31, nets["SPI0_CE0"])
    _c(J2, 32, nets["SPI0_CE1"])
    _c(J2, 34, nets["FAN_PWM"])
    _c(J2, 35, nets["FAN_TACH"])
    _c(J2, 37, nets["PWM_GPIO_1"])
    _c(J2, 38, nets["PWM_GPIO_2"])
    _c(J2, 41, nets["CM5_GPIO_STATUS"])
    for j2_pin in [43, 44, 45, 46, 47, 48, 51, 52, 53, 54, 55, 56, 57, 58, 59, 61]:
        _c(J2, j2_pin, Net(f"CM5_GPIO_HDR_{j2_pin}"))

    # NC every remaining pin
    for J in (J1, J2):
        for n in range(1, 101):
            key = _pin_ref(J, n)
            if not J[key].is_connected():
                J[key] += _NC

    # 5V decoupling near SoM
    for i in range(6):
        c = C(value="10uF", ref=f"C_CM5_BULK_{i+1}",
              footprint="Capacitor_SMD:C_0603_1608Metric")
        c[1] += V5; c[2] += GND
    for i in range(10):
        c = C(value="100nF", ref=f"C_CM5_HF_{i+1}")
        c[1] += V5; c[2] += GND

    return J1, J2
