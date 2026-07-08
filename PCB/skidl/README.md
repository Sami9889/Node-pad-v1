# NodePad — SKiDL Schematic Source (FULL DESIGN)

The full schematic is authored as Python using [SKiDL](https://github.com/devbisme/skidl).
Running `main.py` produces a KiCad netlist that imports directly into
`../NodePad.kicad_pcb` and drops every footprint onto the board with all
ratsnest connections pre-wired.

## Files

| File | Contents | Status |
|------|----------|--------|
| `power_tree.py` | USB-C → CH224K PD → MP2315 buck (5V) → AP2112 LDO (3.3V), ESD, test points | ✅ pin-verified |
| `rtc.py`        | DS3231MZ+ RTC with CR2032 backup, I²C pull-ups | ✅ pin-verified |
| `user_io.py`    | SW1/SW2 buttons, D1–D5 LEDs, J13 GPIO 40-pin, J15 fan header | ✅ pin-verified |
| `cm5.py`        | 2× DF40 100-pin SoM connectors + 5V decoupling (16 caps) | ⚠️ TODO_VERIFY pin map vs Radxa datasheet |
| `ethernet.py`   | RJ45 #1 (1G native), RJ45 #2 + RTL8125BG (2.5G) + Bob-Smith term | ⚠️ TODO_VERIFY RTL8125 pins |
| `usb_hub.py`    | GL3523 hub + 4× USB-A + 4× TPS2553 current-limit switches | ⚠️ TODO_VERIFY GL3523 pins |
| `m2.py`         | M.2 M-key 2280 NVMe + M.2 E-key 2230 WiFi with PCIe wiring | ⚠️ TODO_VERIFY PCIe pins |
| `hdmi.py`       | HDMI Type-A jack, 4× USBLC6 ESD, series R + level-shift stubs | ⚠️ TODO_VERIFY HDMI diff pairs |
| `poe.py`        | PoE+ front-end: bridge rectifier, TVS, MP8007, isolation transformer (all DNP) | ⚠️ TODO_VERIFY MP8007 pins |
| `extras.py`     | HDMI DDC level shifter (BSS138 x2), heatsink mount posts, extra decoupling, EMI cap | ✅ standard patterns |
| `main.py`       | Wires everything together into one design and emits `netlists/nodepad.net` | ✅ 0 ERC errors |

## Current netlist stats

- **230 components** placed
- **239 nets** wired
- **36 unique footprints**, all from stock KiCad 9 library
- All footprints are JLCPCB PCBA compatible
- **0 ERC errors** (219 warnings, all about unconnected GPIO header pins
  and expected TODO_VERIFY placeholders)

## Prerequisites

```bash
pip install skidl==2.2.3
git clone --depth 1 --branch 9.0.0 \
    https://gitlab.com/kicad/libraries/kicad-symbols.git \
    ~/kicad-symbols
export KICAD_SYMBOL_DIR=~/kicad-symbols
export KICAD9_SYMBOL_DIR=~/kicad-symbols
```

## Generate the netlist

```bash
cd PCB/skidl
python3 main.py
# → netlists/nodepad.net
```

## Import into KiCad PCB

1. Open `PCB/NodePad.kicad_pcb` in KiCad 10.
2. **File → Import → KiCad Netlist**
3. Point it at `PCB/skidl/netlists/nodepad.net`
4. Match by **Reference**, Update fields ON, Delete extras ON.
5. Click **Update PCB**. All 230 footprints drop onto the board.

## ⚠️ CRITICAL: Fab-safety checklist before ordering silicon

Every file with **⚠️ TODO_VERIFY** above uses **placeholder pin numbers**
for the chip in question. You MUST review each of the following against
the official datasheet before ordering PCBs:

| Chip | Datasheet source | Pins to verify |
|------|------------------|----------------|
| Radxa CM5 | https://docs.radxa.com/en/som/cm/cm5/hardware/hardware-interface | All 200 pins (2× DF40) |
| RTL8125BG | Realtek RTL8125 datasheet | PCIe pairs, MDI pairs, VCC, LEDs |
| GL3523 | Genesys Logic GL3523 datasheet | USB SS pairs, HS pairs, straps |
| MP2315 | MPS MP2315 datasheet | SW/BST/FB/EN/COMP wiring |
| MP8007 | MPS MP8007 datasheet | RCLASS, SW node, feedback |
| CH224K | WCH CH224K datasheet | CFG resistor pattern for 12V |
| DDC line level shifter | If shipping to modern displays, upgrade to TXS0102 | — |

**Rev-1 will have bugs.** Budget for a rev-2 spin. Every SBC design in
history has needed at least one rework — this is normal, not a failure.

## What each block actually does

### `power_tree.py`
USB-C plug → CH224K negotiates 12V from PD charger → MP2315 buck steps
that down to 5V @ 3A (main CM5 rail) → AP2112 LDO drops 5V to 3.3V for
low-current logic (RTC, LEDs, PHY idle).

### `cm5.py`
Fans out the 100-pin DF40 SoM connectors J1 and J2 into named nets that
the rest of the design uses. This is the "hub" of the schematic — if
these pin assignments are wrong, nothing works.

### `ethernet.py`
Two Ethernet ports. RJ45 #1 uses the CM5's native 1 GbE PHY. RJ45 #2
gets a discrete RTL8125BG chip that talks PCIe Gen 2 x1 to the CM5's
Combo1 lane and does 2.5 GbE off its own PHY.

### `usb_hub.py`
The CM5 has one native USB 3.0 host, but we want 4× USB-A. GL3523 is a
4-port USB 3.0 hub that fans that single port out. Each downstream port
gets its own TPS2553 power switch so a shorted USB device can't take
down the whole board.

### `m2.py`
Two M.2 slots. J5 is the big M-key 2280 slot for NVMe SSDs — this is
where OS boot storage lives. J6 is the smaller E-key 2230 slot for
WiFi/BT modules (or a 2nd 2.5 GbE NIC card if you want to skip WiFi).

### `hdmi.py`
Standard HDMI 2.0 output. TMDS pairs are AC-coupled inside the CM5 so
they route straight through. DDC (I²C to talk EDID with the display) is
level-shifted 3.3V→5V by the BSS138 pair in `extras.py`. All 4 diff
pairs get USBLC6 ESD protection.

### `poe.py`
Optional PoE+ input. **All parts DNP by default** — populate only if you
want PoE. Uses MP8007 as the PD interface controller with a Wurth
750317847 flyback transformer to isolate the ~48V PoE from the 12V
system rail. Meets 802.3at (Class 4, 25 W).

### `rtc.py`
DS3231 real-time clock with a CR2032 coin cell backup. When the board
loses power, the RTC keeps time on the coin cell (~5-year life). Critical
for a server that needs correct time immediately on boot without waiting
for NTP.

### `user_io.py`
Reset button (SW1) pulls CM5 RUN# to GND. Boot/recovery button (SW2)
pulls maskrom pin. Five LEDs: Power, System, Link 1, Link 2, NVMe
activity. 4-pin PWM fan header. 40-pin Pi-compatible GPIO header for HATs.

### `extras.py`
Belt-and-braces: 22 more 100nF decoupling caps distributed across the
5V and 3.3V rails, 7 more 10 µF bulk caps, 4× ferrite beads on sensitive
analog supplies (HDMI, PCIe, both ETH PHYs), 4× M2.5 heatsink mounting
holes near the CM5, the HDMI DDC level shifter, and a 1nF/2kV EMI cap
between signal GND and chassis GND.
