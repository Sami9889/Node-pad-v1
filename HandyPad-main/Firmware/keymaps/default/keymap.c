// Copyright 2026 Samrath "Sami" Singh (@Sami9889)
// SPDX-License-Identifier: GPL-2.0-or-later

#include QMK_KEYBOARD_H
#include <string.h>

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [0] = LAYOUT(
        KC_F13, KC_F14, KC_F15,
        KC_F16, KC_F17, KC_F18, KC_F19
    )
};

#if defined(ENCODER_MAP_ENABLE)
const uint16_t PROGMEM encoder_map[][NUM_ENCODERS][NUM_DIRECTIONS] = {
    [0] = { ENCODER_CCW_CW(KC_VOLD, KC_VOLU) }
};
#endif

/* Encoder push button on GP28 (D2), active low, not in matrix */
static bool enc_btn_pressed = false;
static uint32_t enc_btn_timer = 0;

void keyboard_post_init_user(void) {
    gpio_set_pin_input_high(GP28);
}

void matrix_scan_user(void) {
    bool pin_state = !gpio_read_pin(GP28);
    uint32_t now = timer_read32();

    if (pin_state && !enc_btn_pressed && (now - enc_btn_timer > 5)) {
        enc_btn_pressed = true;
        enc_btn_timer   = now;
        register_code(KC_MUTE);
    } else if (!pin_state && enc_btn_pressed && (now - enc_btn_timer > 5)) {
        enc_btn_pressed = false;
        enc_btn_timer   = now;
        unregister_code(KC_MUTE);
    }
}

#ifdef OLED_ENABLE
/* Animated name banner for Samrath "Sami" Singh.
   The 0.91" 128x32 OLED fits ~21 chars per line with the default 6px font.
   We scroll the name across the screen like a marquee for a lively effect. */
#define OLED_VIEW_COLS 21

static const char PROGMEM sami_marquee[] =
    "Samrath \"Sami\" Singh   *   Sami9889   *   ";
static uint8_t  sami_scroll_pos = 0;
static uint32_t sami_scroll_timer = 0;

bool oled_task_user(void) {
    /* Static title line */
    oled_set_cursor(0, 0);
    oled_write_ln_P(PSTR("=== SamiPad ==="), false);

    /* Advance the marquee on a timer for a smooth animation */
    uint16_t len = strlen_P(sami_marquee);
    if (timer_elapsed32(sami_scroll_timer) > 180) {
        sami_scroll_timer = timer_read32();
        sami_scroll_pos++;
        if (sami_scroll_pos >= len) {
            sami_scroll_pos = 0;
        }
    }

    /* Build the visible window of the scrolling name */
    char view[OLED_VIEW_COLS + 1];
    for (uint8_t i = 0; i < OLED_VIEW_COLS; i++) {
        view[i] = pgm_read_byte(&sami_marquee[(sami_scroll_pos + i) % len]);
    }
    view[OLED_VIEW_COLS] = '\0';

    oled_set_cursor(0, 2);
    oled_write(view, false);

    return false;
}
#endif
