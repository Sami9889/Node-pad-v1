"""
NodePad — User I/O

  - SW1 : reset button (pulls CM5 RUN# to GND, active low)
  - SW2 : boot/recovery button (pulls Maskrom pin to GND at power-on)
  - D1..D5 : status LEDs (Power, System, Link1, Link2, NVMe)
  - J15 : 4-pin PWM fan header
"""

import os
os.environ.setdefault("KICAD_SYMBOL_DIR", "/opt/kicad-libs/symbols")
os.environ.setdefault("KICAD9_SYMBOL_DIR", "/opt/kicad-libs/symbols")

from skidl import Part, Net, TEMPLATE, set_default_tool, KICAD9

set_default_tool(KICAD9)

R = Part("Device", "R", dest=TEMPLATE, footprint="Resistor_SMD:R_0402_1005Metric")


def build_led(net_anode, GND, ref, value, color="Green"):
    """Standard 0603 LED + 1k series resistor to GND."""
    D = Part("Device", "LED",
             value=color,
             ref=ref,
             footprint="LED_SMD:LED_0603_1608Metric")
    R_led = R(value="1k", ref=f"R_{ref}")
    D[1] += net_anode          # anode
    D[2] += R_led[1]           # cathode
    R_led[2] += GND
    return D


def build_button(net_signal, GND, ref, value="Reset"):
    """6x6mm tact switch, one side to signal, other to GND."""
    SW = Part("Switch", "SW_Push",
              value=value,
              ref=ref,
              footprint="Button_Switch_SMD:SW_SPST_TL3305A")
    SW[1] += net_signal
    SW[2] += GND
    # Small pull-up should exist on the CM5 side, but add one here as belt+braces
    return SW


def build_fan_header(V5, GND, TACH, PWM, ref="J15"):
    """Standard 4-pin PC fan header (Molex Mini KK style)."""
    J = Part("Connector_Generic", "Conn_01x04",
             value="Fan",
             ref=ref,
             footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical")
    J[1] += GND      # Fan GND
    J[2] += V5       # Fan +5V (or +12V if we run from VIN)
    J[3] += TACH     # Tach sense
    J[4] += PWM      # PWM control
    # Tach needs pull-up to 3.3V/5V on the CM5 side
    return J


def build(V3P3, V5, GND, SIGNALS):
    """
    Instantiate all user I/O.

    SIGNALS is a dict with these keys:
      RESET_N   : CM5 RUN# (open-drain reset in)
      RECOVERY  : CM5 maskrom/recovery pin
      LED_PWR   : always tied to V3P3 (no CM5 pin needed)
      LED_SYS   : GPIO from CM5 (e.g. GPIO0_B0)
      LED_LNK1  : from RJ45 magnetics LED- pin
      LED_LNK2  : from RTL8125 LED0
      LED_NVME  : from M.2 M-key pin 11 (ACT#)
      FAN_TACH  : CM5 GPIO input
      FAN_PWM   : CM5 PWM output (PWM12)
    """
    # Buttons
    build_button(SIGNALS["RESET_N"],  GND, ref="SW1", value="RESET")
    build_button(SIGNALS["RECOVERY"], GND, ref="SW2", value="BOOT")

    # LEDs
    build_led(V3P3,                  GND, ref="D1", value="PWR",  color="Green")
    build_led(SIGNALS["LED_SYS"],    GND, ref="D2", value="SYS",  color="Blue")
    build_led(SIGNALS["LED_LNK1"],   GND, ref="D3", value="LNK1", color="Yellow")
    build_led(SIGNALS["LED_LNK2"],   GND, ref="D4", value="LNK2", color="Yellow")
    build_led(SIGNALS["LED_NVME"],   GND, ref="D5", value="NVME", color="Red")

    # Fan header
    build_fan_header(V5, GND, SIGNALS["FAN_TACH"], SIGNALS["FAN_PWM"], ref="J15")

    # 40-pin GPIO header (Pi HAT compatible)
    # Placeholder - real pin assignments in DESIGN.md are wired via SIGNALS dict
    J13 = Part("Connector_Generic", "Conn_02x20_Odd_Even",
               value="GPIO40",
               ref="J13",
               footprint="Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical")

    # Power pins on GPIO header (Pi HAT standard)
    J13[1] += V3P3   # pin 1
    J13[17] += V3P3  # pin 17
    J13[2] += V5     # pin 2
    J13[4] += V5     # pin 4
    for gnd_pin in [6, 9, 14, 20, 25, 30, 34, 39]:
        J13[gnd_pin] += GND

    # The remaining pins map to CM5 GPIO — filled in by main.py when it has
    # the SoM connector nets to route into them.
    return J13
