Some files that are used in klipper/klippy/extras <br>
<br>
LPD8806.py - adds support for LPD8806 LEDs in Klipper.<br>
Add the following configuration to your klipper config: <br>
<br>
[LPD8806] <br>
data_pin: <br>
clock_pin: # must be a CLK pin on the mcu<br>
chain_count: <br>
color_order: # add your color order: RGB, RBG, GRB, GBR, BRG or BGR <br>
initial_RED: 0.0 <br>
initial_GREEN: 0.0 <br>
initial_BLUE: 0.0 <br>
