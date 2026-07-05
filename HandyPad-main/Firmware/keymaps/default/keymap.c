#include QMK_KEYBOARD_H

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
bool oled_task_user(void) {
    oled_write_ln_P(PSTR("nilay macropad"), false);
    oled_write_ln_P(PSTR("layer 0"), false);
    return false;
}
#endif
