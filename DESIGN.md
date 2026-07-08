# NodePad — Deep Design Document

Detailed engineering rationale, pin assignments, and layout guidance.
Companion to `README.md` (the marketing/overview doc).

**Revision:** 0.1 (pre-schematic)
**Target SoM:** Radxa CM5 (RK3588S2), 8 GB LPDDR4X, 64 GB eMMC
**PCB stackup:** 4 layers, JLCPCB standard, 1 oz Cu, 1.6 mm thickness
**Board size:** 100 × 100 mm (cheapest JLC tier)

---

## 1. Locked-in decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | PoE circuit | Footprint-only (DNP by default) | Adds ~$8 BOM; make it opt-in for buyers who need it |
| 2 | HDMI | Kept | Costs $1.20; useful for initial setup + hobbyists |
| 3 | 2nd 2.5 GbE NIC | On-board RTL8125BG | Biggest differentiator vs. Pi 5 |
| 4 | USB 3.0 ports | 4× vertical Type-A | Matches Pi 5, useful for NAS builds |
| 5 | License | CERN-OHL-P v2 | Permissive open-hardware, allows commercial |

---

## 2. Radxa CM5 pinout summary

Radxa CM5 uses **2× 100-pin Hirose DF40C-100DS-0.4V** connectors on the underside (0.4 mm pitch, 1.5 mm mated height), matching the Pi CM4 mechanical footprint. Signals differ from CM4 — do NOT reuse CM4 carrier layouts blindly.

**Full pinout reference:** [docs.radxa.com/en/som/cm/cm5](https://docs.radxa.com/en/som/cm/cm5)

Critical signal groups on the CM5:

| Group | Count | Where they go on NodePad |
|---|---|---|
| Power in (5 V) | 6 pins | From MP2315 buck (5V @ 3A) |
| Power in (3.3 V logic) | Internal on module | — |
| GND | 30+ pins | Solid ground pour |
| **PCIe 2.1 x1 (Combo0)** | 4 diff pairs + REFCLK + REFCLK_N + CLKREQ# + PERST# + WAKE# | → **M.2 M-key NVMe** |
| **PCIe 2.1 x1 (Combo1)** *(optional lane)* | Same as above | → **M.2 E-key** (WiFi/2nd NIC) |
| USB 3.0 host | 1× SS RX/TX pair + USB 2.0 pair | → USB 3.0 hub or direct to USB-A #1 |
| USB 2.0 host x2 | 2 pairs | → 40-pin GPIO breakout + USB-A #2 |
| USB 2.0 OTG | 1 pair | → USB-C data (shared with power in) |
| **GbE (native)** | RGMII or SGMII to internal PHY, MDIO/MDC, 4 diff pairs | → RJ45 #1 |
| I²C0/1/3/5 | Multiple | RTC, GPIO header, expansion |
| SPI0/3 | Multiple | GPIO header |
| UART0 (console) | TX/RX | Debug pin header |
| UART2/3/6/8 | RX/TX | GPIO header |
| PWM 0-14 | Various | Fan header (PWM12), GPIO |
| HDMI TX | 3 diff pairs + clock + HPD + CEC + DDC | → HDMI Type-A jack |
| MIPI-DSI (LCD) | 4 lanes + clock | NOT USED (avoid, keep pins free) |
| MIPI-CSI (camera) | 2× ports, 4 lanes each | NOT USED (avoid) |
| SD card | CMD, CLK, DAT0-3 | → microSD push-push socket |
| Boot select | 3-4 pins | → jumper block for eMMC vs SD boot |
| GPIO 40 | GPIO 0-27 | → 40-pin Pi-compatible header |
| Reset | RUN# / RESET# | → SW1 momentary |
| Recovery/Maskrom | ~1 pin | → SW2 momentary |

---

## 3. Peripheral pin assignments (planned)

### 3.1 Power tree

```
USB-C VBUS (5V or PD 5/9/12/15/20V)
        │
        ▼
   CH224K (PD sink; hardcoded 12V request via CFG resistors)
        │
        ▼
   VIN_12V bus  ── to PoE input path (footprint-only)
        │
        ▼
   MP2315 buck → 5V @ 3A ── to CM5 (6 pins), USB hub, fan, LEDs
        │
        ▼
   AP2112K-3.3 LDO → 3.3V_AUX @ 600 mA ── to RTC, RTL8125 idle, logic
```

Total budget:
- Radxa CM5 (worst case, all-cores loaded + NPU): ~9 W → 1.8 A @ 5 V
- NVMe SSD: up to 3 W → 0.6 A @ 5 V
- RTL8125 NIC: ~0.5 W → 0.1 A @ 3.3 V
- USB 3.0 devices (4 ports @ 900 mA each worst-case): 3.6 A @ 5 V (add TPS2553 current limiters — see BOM)
- Total peak: **~15 W** at 5 V → USB-C PD 20 V @ 1 A is safe (fits in 15 W PD profile)

### 3.2 Networking

**NIC #1 (native CM5 GbE PHY, upgraded to 2.5 G later? No — RK3588S PHY is 1 G, use as GbE):**
- Actually route CM5's native GBE_ interface to RJ45 #1 via magnetics
- 4 diff pairs: TXP0/N0, TXP1/N1, TXP2/N2, TXP3/N3 → length matched within 50 mil, 100 Ω differential

Wait — RK3588S has *one* native GbE PHY only. For **dual 2.5 GbE** we need to run **PCIe → RTL8125** for the 2nd port. Decision:

- **RJ45 #1**: CM5 native GbE (1 Gbps) — cheap, always populated
- **RJ45 #2**: RTL8125BG over PCIe 2.1 x1 (2.5 Gbps) — this is the "faster than Pi 5" claim

If we want **dual 2.5 GbE**, add a 2nd RTL8125 to the Combo1 lane at the cost of the M.2 E-key WiFi slot. For rev 1, ship as (1G + 2.5G) which is still better than Pi 5 (single 1G).

**Ethernet magnetics + jack:** Use integrated-magnetics RJ45 (Bel Fuse 0826-1G1T or Halo HFJ11-2450). Center taps → 75Ω Bob Smith termination + 1kV cap to chassis GND.

### 3.3 M.2 slots

- **J5 M-key (2280)**: 4-pin PCIe (Rx±, Tx±) + REFCLK diff pair + PERST# + CLKREQ# + WAKE# → CM5's PCIe Combo0. Standard NVMe pinout. 3.3 V power @ 3 A via dedicated buck if we're paranoid (Pi 5 problem — under-volts on some SSDs). Solution: use MP2315 rail at 3.3 V for M.2 only.
- **J6 E-key (2230)**: 4-pin PCIe (from Combo1) + USB 2.0 pair (from CM5 spare) + I²C + LED + control. Standard WiFi module pinout. 3.3 V power.

### 3.4 USB

CM5 has: 1× USB 3.0 host, 2× USB 2.0 host, 1× USB 2.0 OTG.

For **4× USB-A 3.0** we need a **USB 3.0 hub IC**. Options:
- **GL3523** (Genesys Logic, 4-port USB 3.0 hub) — LCSC C107837, ~$1.80. Popular in Pi HATs.
- **TUSB4041** (TI) — more expensive but rock-solid.

**Decision:** GL3523. Feed it from CM5 USB 3.0 host, output 4× USB-A downstream. Add **4× TPS2553 current limiters** ($0.35 each) for per-port over-current protection.

USB 2.0 ports on CM5:
- Port 0 → OTG → USB-C (shared with power)
- Port 1 → 40-pin GPIO breakout (headers only, for expansion HATs)
- Port 2 → available (route to internal test point or drop)

### 3.5 HDMI

CM5 has HDMI 2.0 TX with 3 diff pairs (TMDS0/1/2) + clock pair + DDC (I²C SDA/SCL) + HPD + CEC.

- Route all 4 diff pairs, length-match within 5 mil, 100 Ω differential
- Add ESD protection: 5 lines × PESD1CAN or similar TVS array
- HDMI Type-A jack: full-size (Molex 47151-1005 or LCSC C2681)

### 3.6 GPIO 40-pin header

Standard **Raspberry Pi HAT-compatible** pinout. Route to `J13`. Pinout mapping:

| Pin | Function | CM5 GPIO |
|---|---|---|
| 1 | 3.3V | — |
| 2 | 5V | — |
| 3 | I²C1 SDA | GPIO1_D0 |
| 4 | 5V | — |
| 5 | I²C1 SCL | GPIO1_D1 |
| 6 | GND | — |
| 7 | GPIO4 | GPIO1_A0 |
| 8 | UART2 TX | GPIO0_B5 |
| 9 | GND | — |
| 10 | UART2 RX | GPIO0_B6 |
| 11 | GPIO17 | GPIO1_A1 |
| 12 | PWM0 | GPIO1_A2 |
| 13 | GPIO27 | GPIO1_A3 |
| 14 | GND | — |
| 15 | GPIO22 | GPIO1_A4 |
| 16 | GPIO23 | GPIO1_A5 |
| 17 | 3.3V | — |
| 18 | GPIO24 | GPIO1_A6 |
| 19 | SPI0 MOSI | GPIO4_B2 |
| 20 | GND | — |
| 21 | SPI0 MISO | GPIO4_B0 |
| 22 | GPIO25 | GPIO1_A7 |
| 23 | SPI0 SCLK | GPIO4_B3 |
| 24 | SPI0 CE0 | GPIO4_B1 |
| 25 | GND | — |
| 26 | SPI0 CE1 | GPIO4_B7 |
| 27 | I²C0 SDA | GPIO4_A0 |
| 28 | I²C0 SCL | GPIO4_A1 |
| 29 | GPIO5 | GPIO4_A2 |
| 30 | GND | — |
| 31 | GPIO6 | GPIO4_A3 |
| 32 | PWM1 | GPIO4_A4 |
| 33 | PWM2 | GPIO4_A5 |
| 34 | GND | — |
| 35 | GPIO19 | GPIO4_A6 |
| 36 | GPIO16 | GPIO4_A7 |
| 37 | GPIO26 | GPIO4_B4 |
| 38 | GPIO20 | GPIO4_B5 |
| 39 | GND | — |
| 40 | GPIO21 | GPIO4_B6 |

*Numbers in "CM5 GPIO" column are provisional — confirm against Radxa datasheet before final routing.*

### 3.7 RTC

DS3231MZ+ (I²C, TCXO, ±5 ppm) on I²C bus shared with system I²C0. Coin cell CR2032 in BT1.
Backup current draw: ~3 µA → ~5-year life on a CR2032.

### 3.8 Fan header

4-pin PC-style header (Molex Mini KK):
1. GND
2. +5V (or +12V if we route from PoE/PD input directly)
3. TACH → CM5 GPIO (input, needs pull-up)
4. PWM (25 kHz) → CM5 PWM12

### 3.9 Buttons + LEDs

- **SW1 Reset**: pulls CM5 RUN# to GND (active low)
- **SW2 Boot**: pulls Maskrom/recovery pin to appropriate level (verify with Radxa datasheet — often GND during power-on)
- **D1 PWR**: green, 3.3V rail
- **D2 SYS**: user-programmable (GPIO)
- **D3 LINK1**: RJ45 #1 link (from PHY)
- **D4 LINK2**: RJ45 #2 link (from RTL8125)
- **D5 NVMe**: activity LED (from M.2 J5 pin 11)

---

## 4. PCB layout strategy (100 × 100 mm)

### 4.1 Component placement zones

```
┌─────────────────────────────────────────────┐
│  RJ45 #1 (1G) │ RJ45 #2 (2.5G) │  USB-C    │  ← REAR I/O EDGE
├─────────────────────────────────────────────┤
│                                             │
│  M.2 E-key (2230)                           │
│  ─────────                                  │
│                                             │
│  ┌──────────────────┐                       │
│  │                  │       HDMI            │
│  │   Radxa CM5      │       USB-A x4        │
│  │   (top center)   │       (right edge)    │
│  │                  │                       │
│  └──────────────────┘                       │
│                                             │
│  M.2 M-key (2280) NVMe                      │
│  ────────────────────────────               │
│                                             │
├─────────────────────────────────────────────┤
│  Power (MP2315, CH224K, AP2112)             │
│  RTC + coin cell    | 40-pin GPIO header    │  ← FRONT EDGE
└─────────────────────────────────────────────┘
```

### 4.2 Layer stackup (JLCPCB standard 4-layer)

| Layer | Purpose | Signal type |
|---|---|---|
| L1 (top) | Signal + component pads | Short-run signals, USB, HDMI, PCIe (short) |
| L2 (inner) | **GND plane** (solid) | Reference plane |
| L3 (inner) | Power planes (5V, 3.3V, VIN) | Split by rail |
| L4 (bottom) | Signal + some component pads | Long-run signals, Ethernet, GPIO |

### 4.3 Design rules (JLCPCB minimums)

| Rule | Value |
|---|---|
| Min track/space | 0.127 mm (5 mil) — safe, JLC free tier allows 3.5 mil |
| Min drill | 0.3 mm PTH |
| Min annular ring | 0.13 mm |
| Min via | 0.3 mm drill / 0.6 mm pad |
| Copper-to-edge | 0.3 mm |
| Silkscreen text | ≥ 1.0 mm height |
| Differential impedance | 90 Ω (USB 2.0) / 100 Ω (USB 3.0, PCIe, Ethernet) |
| Length matching | ±5 mil intra-pair, ±25 mil inter-pair |

### 4.4 High-speed routing priorities

Route order (highest priority first):
1. **PCIe Gen 2** (CM5 ↔ M.2 M-key NVMe): 4 diff pairs, 100Ω, length-match ±5 mil, use L1 with L2 GND ref, avoid vias if possible.
2. **PCIe Gen 2** (CM5 ↔ M.2 E-key): same as above.
3. **USB 3.0** (CM5 ↔ GL3523 hub, hub ↔ USB-A ports): 100Ω diff, length ±5 mil.
4. **HDMI 2.0** (CM5 ↔ HDMI jack): 100Ω diff pairs (TMDS 0/1/2/CLK), length ±5 mil.
5. **Ethernet 2.5G** (RTL8125 ↔ magnetics ↔ RJ45): 100Ω diff, length ±25 mil.
6. **Ethernet 1G** (CM5 ↔ magnetics ↔ RJ45): same.
7. **DDR** — none (on-module, not our problem 🎉).
8. USB 2.0, single-ended low-speed, GPIO — route freely.

### 4.5 Mounting holes

4× M2.5 mounting holes at corners, 3.5 mm from edge (matches Pi HAT stack spec).

- Position: `(3.5, 3.5)`, `(96.5, 3.5)`, `(3.5, 96.5)`, `(96.5, 96.5)` mm
- Drill: 2.75 mm
- Pad: 5.5 mm plated (GND connected)
- Courtyard: 6 mm keep-out radius

---

## 5. What ships in the repo (`/app/`)

```
/app/
├── README.md              — marketing / overview
├── DESIGN.md              — this file
├── BOM.csv                — machine-readable BOM (JLC-format)
├── LICENSE                — CERN-OHL-P v2
├── PCB/
│   ├── NodePad.kicad_pro  — KiCad project
│   ├── NodePad.kicad_sch  — schematic (root sheet)
│   └── NodePad.kicad_pcb  — board (100×100mm outline + mount holes)
├── CAD/                   — 3D-printable case (to be designed after Rev 2)
├── Firmware/              — bootloader configs, device tree (Rev 2)
├── Production/            — outputs after final export
│   ├── gerbers.zip
│   ├── bom.csv
│   ├── cpl.csv
│   └── assembly.pdf
└── docs/
    └── quick-start.md
```

---

## 6. Known risks (to address before spending prototype money)

1. **PCIe REFCLK routing** — Radxa doesn't guarantee CM5's PCIe REFCLK is exposed cleanly. If not, we need an external 100 MHz LVDS clock (e.g. Si53156). Verify in schematic phase.
2. **USB 3.0 hub bring-up** — GL3523 is finicky about strap resistors on power-on. Follow reference schematic exactly.
3. **PoE isolation** — if populated, PoE side needs proper isolation (1500 V rated transformer, minimum 4 mm creepage on both sides of transformer, per IEEE 802.3at). This means physical keep-out zones on PCB.
4. **CM5 thermals** — RK3588S under load hits 85°C without a heatsink. Design case with mandatory heatsink pad.
5. **RTL8125 EMC** — 2.5GbE PHY is sensitive to poor grounding. Solid ground pour under PHY IC + magnetics + jack.

---

## 7. Milestones

- [x] Design brief locked (this document)
- [ ] KiCad project scaffold (`.kicad_pro`, blank sheet, board outline)
- [ ] Schematic capture — power tree
- [ ] Schematic capture — CM5 connectors + decoupling
- [ ] Schematic capture — NIC (RTL8125) + magnetics
- [ ] Schematic capture — M.2 slots + USB hub
- [ ] Schematic capture — HDMI, GPIO, RTC, buttons, LEDs
- [ ] Schematic capture — PoE section (footprint-only, DNP)
- [ ] ERC clean
- [ ] Footprint assignment (JLC-Basic priority)
- [ ] PCB placement
- [ ] PCB routing (high-speed → low-speed)
- [ ] DRC clean
- [ ] Gerber + CPL + BOM export
- [ ] Order 5 prototypes (~$400)
- [ ] Bring-up + rev 2 fixes
- [ ] Sellable rev 2 spin

---

*This document evolves as decisions are made and validated. Every change should include a date + author note in a changelog appendix (to be added).*
