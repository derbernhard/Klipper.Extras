# Support for "LPD8806" leds based on klippper "dotstar.py"
#
# Copyright (C) 2025 - 2030 derBernhard
#
# This file may be distributed under the terms of the GNU GPLv3 license.
#
# --- Klipper config ---
#
# [LPD8806]
# data_pin: 
# clock_pin: 
# chain_count: 
# color_order: # add your color order: RGB, RBG, GRB, GBR, BRG or BGR
# initial_RED: 0.0
# initial_GREEN: 0.0
# initial_BLUE: 0.0
#


from . import bus, led

BACKGROUND_PRIORITY_CLOCK = 0x7fffffff00000000

class LPD8806:
    def __init__(self, config):
        self.printer = printer = config.get_printer()
        # Configure a software spi bus
        ppins = printer.lookup_object('pins')
        data_pin_params = ppins.lookup_pin(config.get('data_pin'))
        clock_pin_params = ppins.lookup_pin(config.get('clock_pin'))
        mcu = data_pin_params['chip']
        if mcu is not clock_pin_params['chip']:
            raise config.error("Dotstar pins must be on same mcu")
        sw_spi_pins = (data_pin_params['pin'], data_pin_params['pin'],
                       clock_pin_params['pin'])
        self.spi = bus.MCU_SPI(mcu, None, None, 0, 1000000, sw_spi_pins)  # 1 MHz clock for LPD8806
        # Check color order
        self.color_order = config.get('color_order', 'RGB')  # Standard: RGB
        # Initialize color data
        self.chain_count = config.getint('chain_count', 1, minval=1)
        self.led_helper = led.LEDHelper(config, self.update_leds,
                                        self.chain_count)
        self.prev_data = None
        # Register commands
        printer.register_event_handler("klippy:connect", self.handle_connect)

        # Create gamma correction
        self.gamma = [0x80 | int(
            pow(float(i) / 255.0, 2.5) * 127.0 + 0.5) for i in range(256)]

    def handle_connect(self):
        self.update_leds(self.led_helper.get_status()['color_data'], None)

    def update_leds(self, led_state, print_time):
        if led_state == self.prev_data:
            return
        self.prev_data = led_state

        # Calculate latchBytes
        self._latchBytes = (self.chain_count + 31) // 32  # 3 Bytes pro LED
        self._buf = []

        # Add latchBytes
        for _ in range(0, self._latchBytes):
            self._buf.append(0)

        data = [0] * (len(led_state) * 3 +1)
        for i, (red, green, blue, _) in enumerate(led_state):
            idx = i * 3
            gamma_red = self.gamma[int(red * 255)]
            gamma_green = self.gamma[int(green * 255)]
            gamma_blue = self.gamma[int(blue * 255)]

            if self.color_order == 'RGB':
                data[idx] = gamma_green
                data[idx + 1] = gamma_red
                data[idx + 2] = gamma_blue
            elif self.color_order == 'RBG':
                data[idx] = gamma_red
                data[idx + 1] = gamma_blue
                data[idx + 2] = gamma_green
            elif self.color_order == 'GRB':
                data[idx] = gamma_green
                data[idx + 1] = gamma_blue
                data[idx + 2] = gamma_red
            elif self.color_order == 'GBR':
                data[idx] = gamma_green
                data[idx + 1] = gamma_blue
                data[idx + 2] = gamma_red
            elif self.color_order == 'BRG':
                data[idx] = gamma_blue
                data[idx + 1] = gamma_red
                data[idx + 2] = gamma_green
            elif self.color_order == 'BGR':
                data[idx] = gamma_blue
                data[idx + 1] = gamma_green
                data[idx + 2] = gamma_red

        if len(led_state) > 0:
            led_state[-1] = (0, 0, 0, 0)

        self._buf.extend(data)

        minclock = 0
        if print_time is not None:
            minclock = self.spi.get_mcu().print_time_to_clock(print_time)

        for d in [self._buf[i:i + 20] for i in range(0, len(self._buf), 20)]:
            self.spi.spi_send(d, minclock=minclock, reqclock=BACKGROUND_PRIORITY_CLOCK)

    def get_status(self, eventtime):
        return self.led_helper.get_status(eventtime)

def load_config(config):
    return LPD8806(config)
