"""
NodePad-Net — Networking variant main.

Same base as NodePad but with:
  * 2× 2.5 GbE (adds a second RTL8125BG on PCIe1)
  * 1× SFP cage (1G fiber uplink over SGMII)
  * 1× 1 GbE (CM5 native, kept for management)
  * NO M.2 E-key slot (PCIe1 goes to RTL8125-2 instead of WiFi)
  * Trimmed USB: 2× USB-A instead of 4× (more room for RJ45s + SFP)
  * NO HDMI (headless router/switch appliance)

Everything else identical to the base NodePad:
  * Radxa CM5 SoM
  * USB-C PD input, MP2315 buck, AP2112 LDO
  * M.2 M-key 2280 NVMe (still important for boot storage)
  * RTC + coin cell
  * Buttons + LEDs + fan + heatsink mounts

Run:
    KICAD_SYMBOL_DIR=/opt/kicad-libs/symbols python3 main_net.py

Outputs:
    netlists/nodepad_net.net
"""

import os
os.environ.setdefault("KICAD_SYMBOL_DIR", "/opt/kicad-libs/symbols")
os.environ.setdefault("KICAD9_SYMBOL_DIR", "/opt/kicad-libs/symbols")

from skidl import Net, generate_netlist, ERC, set_default_tool, KICAD9

set_default_tool(KICAD9)


def make_net(name, drive=None):
    n = Net(name)
    if drive is not None:
        n.drive = drive
    return n


# Same shared nets as main.py
nets = {
    "GND":       make_net("GND", drive=3),
    "+5V":       make_net("+5V"),
    "+3V3_AUX":  make_net("+3V3_AUX"),
    "VIN_12V":   make_net("VIN_12V"),
    "VBUS_USB":  make_net("VBUS_USB"),
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
    "I2C0_SDA":  make_net("I2C0_SDA"),
    "I2C0_SCL":  make_net("I2C0_SCL"),
    "I2C1_SDA":  make_net("I2C1_SDA"),
    "I2C1_SCL":  make_net("I2C1_SCL"),
    "UART0_TX":  make_net("UART0_TX"),
    "UART0_RX":  make_net("UART0_RX"),
    "UART2_TX":  make_net("UART2_TX"),
    "UART2_RX":  make_net("UART2_RX"),
    "SPI0_MOSI": make_net("SPI0_MOSI"),
    "SPI0_MISO": make_net("SPI0_MISO"),
    "SPI0_SCLK": make_net("SPI0_SCLK"),
    "SPI0_CE0":  make_net("SPI0_CE0"),
    "SPI0_CE1":  make_net("SPI0_CE1"),
    "PWM_GPIO_1": make_net("PWM_GPIO_1"),
    "PWM_GPIO_2": make_net("PWM_GPIO_2"),

    # HDMI nets exist so cm5.py can reference them; unused in this variant
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

    # Ethernet #1 native GbE
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

    # Ethernet #2 (first RTL8125, shares Combo0 - wait, we need it on its own lane)
    # Actually for this variant we keep #2 on Combo0 (shared with NVMe? No, dedicate)
    # Simpler: keep ethernet.py's RTL8125 on PCIE1 (its default),
    # AND add a second RTL8125 also on PCIE1 via a PCIe switch OR use PCIE0 for one of them.
    # For rev1 scaffold: repurpose Combo0 to a PCIe switch chip if needed.
    # For now, both RTL8125s share PCIE1 declaration but note in comment.
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

    # Ethernet #3 - second 2.5G RTL8125
    "ETH2_MDI0_P": make_net("ETH2_MDI0_P"),
    "ETH2_MDI0_N": make_net("ETH2_MDI0_N"),
    "ETH2_MDI1_P": make_net("ETH2_MDI1_P"),
    "ETH2_MDI1_N": make_net("ETH2_MDI1_N"),
    "ETH2_MDI2_P": make_net("ETH2_MDI2_P"),
    "ETH2_MDI2_N": make_net("ETH2_MDI2_N"),
    "ETH2_MDI3_P": make_net("ETH2_MDI3_P"),
    "ETH2_MDI3_N": make_net("ETH2_MDI3_N"),
    "ETH2_LED_ACT":  make_net("ETH2_LED_ACT"),
    "ETH2_LED_LINK": make_net("ETH2_LED_LINK"),

    # SFP
    "SFP_TX_P": make_net("SFP_TX_P"),
    "SFP_TX_N": make_net("SFP_TX_N"),
    "SFP_RX_P": make_net("SFP_RX_P"),
    "SFP_RX_N": make_net("SFP_RX_N"),

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

    # PCIe Combo1 (both RTL8125s share via bifurcation OR one goes here)
    "PCIE1_TX_P":     make_net("PCIE1_TX_P"),
    "PCIE1_TX_N":     make_net("PCIE1_TX_N"),
    "PCIE1_RX_P":     make_net("PCIE1_RX_P"),
    "PCIE1_RX_N":     make_net("PCIE1_RX_N"),
    "PCIE1_REFCLK_P": make_net("PCIE1_REFCLK_P"),
    "PCIE1_REFCLK_N": make_net("PCIE1_REFCLK_N"),
    "PCIE1_PERST_N":  make_net("PCIE1_PERST_N"),
    "PCIE1_CLKREQ_N": make_net("PCIE1_CLKREQ_N"),
    "PCIE1_WAKE_N":   make_net("PCIE1_WAKE_N"),

    # SD + boot
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

    # CM5 control
    "CM5_RUN_N":       make_net("CM5_RUN_N"),
    "CM5_MASKROM":     make_net("CM5_MASKROM"),
    "CM5_POWER_EN":    make_net("CM5_POWER_EN"),
    "CM5_PWR_GOOD":    make_net("CM5_PWR_GOOD"),
    "CM5_GPIO_STATUS": make_net("CM5_GPIO_STATUS"),

    "FAN_TACH": make_net("FAN_TACH"),
    "FAN_PWM":  make_net("FAN_PWM"),
    "NVME_ACT_N": make_net("NVME_ACT_N"),
    "RTC_INT_N":  make_net("RTC_INT_N"),
}


# ----- Compose the -Net variant -------------------------------------

import power_tree      # noqa: F401  (auto-instantiates on import)

import cm5;         cm5.build(nets)
import ethernet;    ethernet.build(nets)             # 1st RTL8125 + native GbE
import ethernet_net; ethernet_net.build(nets)        # 2nd RTL8125 (2.5G #3)
import sfp;         sfp.build(nets)                  # SFP cage
import m2;          m2.build(nets)                   # NVMe (E-key hosts nothing here)
# NO hdmi in networking variant
import poe;         poe.build(nets)                  # PoE optional (DNP)
import rtc
rtc.build(V3P3=nets["+3V3_AUX"], GND=nets["GND"],
          SDA=nets["I2C0_SDA"], SCL=nets["I2C0_SCL"],
          INT_N=nets["RTC_INT_N"])

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

import extras;      extras.build(nets)


# ----- Emit netlist ---------------------------------------------------
if __name__ == "__main__":
    os.makedirs("netlists", exist_ok=True)
    ERC()
    generate_netlist(file_="netlists/nodepad_net.net")
    print("[OK] NodePad-Net netlist -> netlists/nodepad_net.net")
