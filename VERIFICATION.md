# NodePad — Pin & Function Verification Pass

Rev 0.1 · Author: Samrath "Sami" Singh · Date: 2026-07-08

This is an honest self-audit of every component & subsystem, sorted by
confidence level. Use it as a checklist before ordering silicon.

---

## ✅ VERIFIED — safe to fab as-is

These come from standard specs / well-documented parts / pinouts baked
into the KiCad standard library. If it says ✅ here, it's actually right.

| Part | Ref | Verified | Source |
|------|-----|----------|--------|
| USB-C receptacle | J7 | Pinout matches USB-IF Type-C spec r2.1 | USB-IF |
| RJ45 jacks (T568B) | J3, J4, J21 | Pins 1-8 mapped correctly to 4 MDI pairs | TIA-568B |
| HDMI Type-A | J12 | 3× TMDS + clock + DDC + CEC + HPD + 5V per HDMI 2.0 | HDMI Licensing |
| DS3231MZ+ | U7 | Pin names verified from KiCad `Timer_RTC` library | KiCad lib |
| AP2112K-3.3 | U4 | SOT-23-5: 1=VIN, 2=GND, 3=EN, 4=NC, 5=VOUT (from KiCad `Regulator_Linear`) | KiCad lib |
| BSS138 NMOS | Q_DDC_1, Q_DDC_2 | Standard GDS SOT-23 pinout (level shifter) | Fairchild |
| USBLC6-2SC6 | U8, U9, U_HDMI_ESD_1..4 | I/O1, I/O2, VBUS, GND per ST datasheet (in KiCad `Power_Protection`) | KiCad lib |
| CR2032 holder | BT1 | 2-pin battery holder, standard | Keystone 3002 |
| Tactile switch | SW1, SW2 | 2-pin momentary, standard | LCSC C318884 |
| LEDs (0603) | D1-D5 | Anode/cathode, 1kΩ series R → GND | Standard |
| Bob-Smith termination | R_BS_* | 8× 75Ω + 1nF/2kV cap to chassis GND | Ethernet Alliance recommendation |
| M.2 M-key power/GND | J5 (pins 69-75) | Matches JEDEC MO-297 M-key spec | JEDEC |
| M.2 E-key power/GND | J6 | Matches MO-297 E-key spec | JEDEC |
| Test points | TP1-TP5 | Single-pin pads on power rails, standard | Custom |
| Mounting holes | MH1-MH4 | M2.5 clearance holes near CM5 for heatsink | Radxa CM5 heatsink pattern |
| Fan header | J15 | 4-pin PC-style: GND/+5V/TACH/PWM | Intel 4-wire fan spec |
| GPIO 40-pin | J13 | Pi HAT compatible: 3.3V/5V/GND/GPIO per Raspberry Pi HAT+ spec | RPi HAT specification |

---

## ⚠️ TODO_VERIFY — placeholder pin numbers, MUST review before fab

These pin numbers are best-guess and **will not match the real chip's
datasheet**. For each row below, open the linked datasheet PDF and
correct the SKiDL source before regenerating the netlist.

| Part | Ref | Source of truth | Risk if wrong |
|------|-----|-----------------|---------------|
| **Radxa CM5 SoM** | J1, J2 | [docs.radxa.com/en/som/cm/cm5/hardware/hardware-interface](https://docs.radxa.com/en/som/cm/cm5/hardware/hardware-interface) | Dead board, no boot |
| RTL8125BG (2.5GbE PHY+MAC) | U2, U15 | Realtek RTL8125BG datasheet (request from Realtek) | No 2.5G network |
| GL3523 (USB 3.0 hub) | U10 | Genesys Logic GL3523 datasheet | No USB downstream |
| MP2315 (5V buck) | U3 | MPS MP2315 datasheet | Wrong output voltage or oscillation |
| MP8007 (PoE PD) | U6 | MPS MP8007 datasheet (only if you populate PoE) | PoE fails to negotiate |
| CH224K (USB-C PD sink) | U5 | WCH CH224K datasheet | Only 5V from USB-C, no PD |
| TPS2553 (USB port switch) | U11-U14 | TI TPS2553 datasheet | No per-port current limit |

**Typical review time**: ~2-3 hours per chip if you're methodical.
Budget one long afternoon for the whole set.

---

## 🆕 Added in this verification pass

These were missing from the original build; added now:

1. **Boot-select pull-up resistors** on `CM5_BOOT0/1/2` (10 kΩ to 3.3V) so CM5 boots from eMMC by default.
2. **Reset button debouncing cap** (100 nF from RESET_N to GND) on `SW1` — prevents contact bounce false-triggering.
3. **Power sequencing delay resistor + cap** (RC filter on CM5_POWER_EN) so the SoM ramps its internal rails only after 5V is stable.
4. **VIN_12V bulk cap** (47 µF electrolytic + 100 nF) at the input to MP2315 — reduces switching ripple back to the PD source.
5. **PCIe REFCLK bias resistors** — 100 Ω differential termination + 0 Ω DNP option resistors near the M.2 slot connector.
6. **NVMe activity LED pull-up** — the M.2 activity pin is open-drain; needs a pull-up to be visible.
7. **Extra ground stitching via** callouts documented in `extras.py` comments (via-fence around the SFP + high-speed lanes).

---

## 🛠️ What each part actually does (in plain English)

| Refs | Function |
|------|----------|
| U1 (Radxa CM5) | The whole computer — 8-core ARM CPU + GPU + 8 GB RAM + 64 GB eMMC. Everything else on this board is just I/O around it. |
| J1, J2 | The two 100-pin connectors the CM5 module plugs into. |
| U3, U4, U5 | Power converters: turn USB-C 5V or PD 12V into stable 5V (for CM5) and 3.3V (for RTC/LEDs/PHYs). |
| J7 | USB-C jack — main power input and OTG data. |
| U2, J3, J4 | Ethernet section: 1 GbE port from CM5's native PHY (J3), plus 2.5 GbE port via RTL8125 chip (J4). |
| U10, J8-J11, U11-U14 | USB 3.0 hub (U10) fans out CM5's single USB3 port into 4× USB-A. TPS2553 chips give each port its own current limit so a bad USB device can't crash the board. |
| J5 | M.2 socket for an NVMe SSD (OS install lives here, not on the microSD). |
| J6 | Smaller M.2 socket for a WiFi/BT card (or 2nd network card). |
| J12 | HDMI monitor output. |
| J13 | 40-pin GPIO header — same pinout as a Raspberry Pi, so HATs work. |
| J14 | microSD slot — for fallback boot / recovery. |
| J15 | 4-pin PC-style fan header for cooling. |
| MH1-MH4 | Screw holes for bolting a heatsink onto the CM5. |
| U7, BT1 | Real-time clock chip + coin cell — keeps time when the board loses power. |
| SW1, SW2 | Reset button and Boot/Recovery button. |
| D1-D5 | Status LEDs: Power / System / Link1 / Link2 / NVMe activity. |
| U6, T1 | Optional PoE circuit (not populated by default) — lets you power the board over Ethernet. |
| J20 | SFP cage (Net variant only) — for a 1G fiber transceiver. |
| U15, J21 | 2nd 2.5GbE port (Net variant only). |

---

## 🔥 Cooling recommendation (spelled out)

The RK3588S in the CM5 hits **85°C sustained** under load without cooling. Your options:

1. **Radxa CM5 IO Heatsink** (~$5 on Aliexpress) — passive aluminum, screws into the MH1-MH4 holes. Adequate for idle-to-medium load.
2. **Radxa CM5 Active Heatsink** (~$12) — same base with a small 30 mm 5V fan on top. Handles sustained full load.
3. **DIY** — 25 × 25 × 10 mm aluminum block + thermal pad + 5V fan on J15 header. ~$5 in parts.

Fan header (J15) is wired: pin 1 GND, pin 2 +5V, pin 3 TACH (rpm sense), pin 4 PWM (speed control). Standard Intel 4-wire fan pinout, so any PC-style 4-pin fan works.

---

## 🚨 The one thing that would actually kill Rev 1

If I had to pick one single failure mode most likely to brick the first prototype: **CM5 5V supply pins wired wrong or not enough of them.** The RK3588S needs ~2 A at peak load; if we only route 1-2 of the 6 dedicated 5V input pins on the DF40 connector, you get a brownout under load.

**Mitigation** (already in `cm5.py`): Pins 1-6 on J1 all tied to +5V, plus 16 bulk decoupling caps distributed across the SoM area. Should hold up under 3 A instantaneous.

But — **verify pins 1-6 on your J1 actually correspond to +5V input on the Radxa CM5 datasheet.** If Radxa uses e.g. pins A1-A3 + B1-B3 for +5V instead, my numeric-to-A/B mapping (`_c()` helper in `cm5.py`) needs re-checking.
