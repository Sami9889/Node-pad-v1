"""
NodePad — Main schematic composition (FULL design).

Composes all sub-blocks into a single design and emits the KiCad netlist.

Sub-blocks:
    power_tree.py     Power (USB-C -> PD -> buck -> LDO)
    cm5.py            Radxa CM5 SoM connectors J1/J2
    ethernet.py       RJ45 #1 (1G native) + RTL8125 + RJ45 #2 (2.5G)
    usb_hub.py        GL3523 hub + 4x USB-A + TPS2553 power switches
    m2.py             M.2 M-key NVMe + M.2 E-key WiFi
    hdmi.py           HDMI 2.0 Type-A + ESD
    poe.py            PoE+ front-end (all DNP by default)
    rtc.py            DS3231 + CR2032 backup
    user_io.py        Buttons, LEDs, GPIO40, fan header

Run:
    KICAD_SYMBOL_DIR=/opt/kicad-libs/symbols \\
    python3 main.py

Outputs:
    ./netlists/nodepad.net
"""

import os
os.environ.setdefault("KICAD_SYMBOL_DIR", "/opt/kicad-libs/symbols")
os.environ.setdefault("KICAD9_SYMBOL_DIR", "/opt/kicad-libs/symbols")

from skidl import Net, generate_netlist, ERC, set_default_tool, KICAD9

set_default_tool(KICAD9)


# ---------------------------------------------------------------------------
# Declare every net that crosses sub-block boundaries FIRST
# so sub-blocks all bind to the same instance.
# ---------------------------------------------------------------------------
def make_net(name, drive=None):
    n = Net(name)
    if drive is not None:
        n.drive = drive
    return n


nets = {
    # Power rails (already created by power_tree - we'll reuse by name)
    "GND":       make_net("GND", drive=3),
    "+5V":       make_net("+5V"),
    "+3V3_AUX":  make_net("+3V3_AUX"),
    "VIN_12V":   make_net("VIN_12V"),
    "VBUS_USB":  make_net("VBUS_USB"),

    # USB 2.0 (OTG) and USB 3.0 host (CM5)
    "USB_DP":    make_net("USB_DP"),
    "USB_DM":    make_net("USB_DM"),
    "USB3_TX_P": make_net("USB3_TX_P"),
    "USB3_TX_N": make_net("USB3_TX_N"),
    "USB3_RX_P": make_net("USB3_RX_P"),
    "USB3_RX_N": make_net("USB3_RX_N"),
    "USB3_DP":   make_net("USB3_DP"),
    "USB3_DM":   make_net("USB3_DM"),
    "USB2_1_DP": make_net("USB2_1_DP"),
    "USB2_1_DM": make_net("USB2_1_DM"),
    "USB2_2_DP": make_net("USB2_2_DP"),
    "USB2_2_DM": make_net("USB2_2_DM"),

    # I²C busses
    "I2C0_SDA":  make_net("I2C0_SDA"),
    "I2C0_SCL":  make_net("I2C0_SCL"),
    "I2C1_SDA":  make_net("I2C1_SDA"),
    "I2C1_SCL":  make_net("I2C1_SCL"),

    # UART
    "UART0_TX":  make_net("UART0_TX"),
    "UART0_RX":  make_net("UART0_RX"),
    "UART2_TX":  make_net("UART2_TX"),
    "UART2_RX":  make_net("UART2_RX"),

    # SPI
    "SPI0_MOSI": make_net("SPI0_MOSI"),
    "SPI0_MISO": make_net("SPI0_MISO"),
    "SPI0_SCLK": make_net("SPI0_SCLK"),
    "SPI0_CE0":  make_net("SPI0_CE0"),
    "SPI0_CE1":  make_net("SPI0_CE1"),

    # PWM
    "PWM_GPIO_1": make_net("PWM_GPIO_1"),
    "PWM_GPIO_2": make_net("PWM_GPIO_2"),

    # HDMI (CM5 -> J12)
    "HDMI_TX0_P": make_net("HDMI_TX0_P"),
    "HDMI_TX0_N": make_net("HDMI_TX0_N"),
    "HDMI_TX1_P": make_net("HDMI_TX1_P"),
    "HDMI_TX1_N": make_net("HDMI_TX1_N"),
    "HDMI_TX2_P": make_net("HDMI_TX2_P"),
    "HDMI_TX2_N": make_net("HDMI_TX2_N"),
    "HDMI_CLK_P": make_net("HDMI_CLK_P"),
    "HDMI_CLK_N": make_net("HDMI_CLK_N"),
    "HDMI_CEC":   make_net("HDMI_CEC"),
    "HDMI_HPD":   make_net("HDMI_HPD"),
    "HDMI_DDC_SDA": make_net("HDMI_DDC_SDA"),
    "HDMI_DDC_SCL": make_net("HDMI_DDC_SCL"),

    # Ethernet #1 (CM5 native GbE MDI)
    "ETH0_MDI0_P": make_net("ETH0_MDI0_P"),
    "ETH0_MDI0_N": make_net("ETH0_MDI0_N"),
    "ETH0_MDI1_P": make_net("ETH0_MDI1_P"),
    "ETH0_MDI1_N": make_net("ETH0_MDI1_N"),
    "ETH0_MDI2_P": make_net("ETH0_MDI2_P"),
    "ETH0_MDI2_N": make_net("ETH0_MDI2_N"),
    "ETH0_MDI3_P": make_net("ETH0_MDI3_P"),
    "ETH0_MDI3_N": make_net("ETH0_MDI3_N"),
    "ETH0_LED_ACT":  make_net("ETH0_LED_ACT"),
    "ETH0_LED_LINK": make_net("ETH0_LED_LINK"),

    # Ethernet #2 (RTL8125 MDI + LEDs)
    "ETH1_MDI0_P": make_net("ETH1_MDI0_P"),
    "ETH1_MDI0_N": make_net("ETH1_MDI0_N"),
    "ETH1_MDI1_P": make_net("ETH1_MDI1_P"),
    "ETH1_MDI1_N": make_net("ETH1_MDI1_N"),
    "ETH1_MDI2_P": make_net("ETH1_MDI2_P"),
    "ETH1_MDI2_N": make_net("ETH1_MDI2_N"),
    "ETH1_MDI3_P": make_net("ETH1_MDI3_P"),
    "ETH1_MDI3_N": make_net("ETH1_MDI3_N"),
    "ETH1_LED_ACT":  make_net("ETH1_LED_ACT"),
    "ETH1_LED_LINK": make_net("ETH1_LED_LINK"),

    # PCIe Combo0 (M-key NVMe)
    "PCIE0_TX_P":     make_net("PCIE0_TX_P"),
    "PCIE0_TX_N":     make_net("PCIE0_TX_N"),
    "PCIE0_RX_P":     make_net("PCIE0_RX_P"),
    "PCIE0_RX_N":     make_net("PCIE0_RX_N"),
    "PCIE0_REFCLK_P": make_net("PCIE0_REFCLK_P"),
    "PCIE0_REFCLK_N": make_net("PCIE0_REFCLK_N"),
    "PCIE0_PERST_N":  make_net("PCIE0_PERST_N"),
    "PCIE0_CLKREQ_N": make_net("PCIE0_CLKREQ_N"),
    "PCIE0_WAKE_N":   make_net("PCIE0_WAKE_N"),

    # PCIe Combo1 (E-key or RTL8125)
    "PCIE1_TX_P":     make_net("PCIE1_TX_P"),
    "PCIE1_TX_N":     make_net("PCIE1_TX_N"),
    "PCIE1_RX_P":     make_net("PCIE1_RX_P"),
    "PCIE1_RX_N":     make_net("PCIE1_RX_N"),
    "PCIE1_REFCLK_P": make_net("PCIE1_REFCLK_P"),
    "PCIE1_REFCLK_N": make_net("PCIE1_REFCLK_N"),
    "PCIE1_PERST_N":  make_net("PCIE1_PERST_N"),
    "PCIE1_CLKREQ_N": make_net("PCIE1_CLKREQ_N"),
    "PCIE1_WAKE_N":   make_net("PCIE1_WAKE_N"),

    # SD card + boot select
    "SD_CLK": make_net("SD_CLK"),
    "SD_CMD": make_net("SD_CMD"),
    "SD_D0":  make_net("SD_D0"),
    "SD_D1":  make_net("SD_D1"),
    "SD_D2":  make_net("SD_D2"),
    "SD_D3":  make_net("SD_D3"),
    "SD_DET_N": make_net("SD_DET_N"),
    "CM5_BOOT0": make_net("CM5_BOOT0"),
    "CM5_BOOT1": make_net("CM5_BOOT1"),
    "CM5_BOOT2": make_net("CM5_BOOT2"),

    # CM5 control signals
    "CM5_RUN_N":       make_net("CM5_RUN_N"),
    "CM5_MASKROM":     make_net("CM5_MASKROM"),
    "CM5_POWER_EN":    make_net("CM5_POWER_EN"),
    "CM5_PWR_GOOD":    make_net("CM5_PWR_GOOD"),
    "CM5_GPIO_STATUS": make_net("CM5_GPIO_STATUS"),

    # I/O signals (fan, buttons already-known)
    "FAN_TACH": make_net("FAN_TACH"),
    "FAN_PWM":  make_net("FAN_PWM"),
    "NVME_ACT_N": make_net("NVME_ACT_N"),
    "RTC_INT_N":  make_net("RTC_INT_N"),

    # Aliases used by user_io.build()
    "PHY1_LED_ACT": None,  # will be aliased to ETH0_LED_ACT below
    "PHY2_LED_ACT": None,
}
# Alias PHYx_LED_ACT -> ETHx_LED_ACT
nets["PHY1_LED_ACT"] = nets["ETH0_LED_ACT"]
nets["PHY2_LED_ACT"] = nets["ETH1_LED_ACT"]


# ---------------------------------------------------------------------------
# Instantiate sub-blocks in dependency order
# ---------------------------------------------------------------------------

# Power tree runs on import (still uses its own local Net() instances but
# de-duplicates by name — the top-level nets we made above will merge in
# because Net() with same name = same net).
import power_tree  # noqa: F401

# CM5 SoM connectors
import cm5
cm5.build(nets)

# Ethernet
import ethernet
ethernet.build(nets)

# USB hub + 4x USB-A
import usb_hub
usb_hub.build(nets)

# M.2 slots
import m2
m2.build(nets)

# HDMI
import hdmi
hdmi.build(nets)

# PoE (optional, all DNP)
import poe
poe.build(nets)

# RTC
import rtc
rtc.build(V3P3=nets["+3V3_AUX"], GND=nets["GND"],
          SDA=nets["I2C0_SDA"], SCL=nets["I2C0_SCL"],
          INT_N=nets["RTC_INT_N"])

# User I/O
import user_io
user_io.build(
    V3P3=nets["+3V3_AUX"],
    V5=nets["+5V"],
    GND=nets["GND"],
    SIGNALS={
        "RESET_N":   nets["CM5_RUN_N"],
        "RECOVERY":  nets["CM5_MASKROM"],
        "LED_SYS":   nets["CM5_GPIO_STATUS"],
        "LED_LNK1":  nets["ETH0_LED_ACT"],
        "LED_LNK2":  nets["ETH1_LED_ACT"],
        "LED_NVME":  nets["NVME_ACT_N"],
        "FAN_TACH":  nets["FAN_TACH"],
        "FAN_PWM":   nets["FAN_PWM"],
    },
)


# Extras (heatsink mount, HDMI level shifter, more decoupling)
import extras
extras.build(nets)


import missing_parts
missing_parts.build(nets)


# ---------------------------------------------------------------------------
# Emit netlist
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    os.makedirs("netlists", exist_ok=True)
    ERC()
    generate_netlist(file_="netlists/nodepad.net")
    print("[OK] Combined netlist -> netlists/nodepad.net")
