import board
import gc
import terminalio
import time
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_requests as requests

# from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
from adafruit_lis3dh import LIS3DH_I2C
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
from busio import I2C
from displayio import Group

FONT = terminalio.FONT

from app.constants import (
    DEBUG,
    BRIGHTNESS,
    NTP_INTERVAL,
    MATRIX_WIDTH,
    MATRIX_HEIGHT,
    MATRIX_BIT_DEPTH,
    MATRIX_COLOR_ORDER,
    MQTT_PREFIX,
)

from app.utils import logger, matrix_rotation, get_new_epochs

logger(
    f"debug={DEBUG} brightness={BRIGHTNESS} ntp_interval={NTP_INTERVAL} mqtt_prefix={MQTT_PREFIX}"
)
logger(
    f"matrix_width={MATRIX_WIDTH} matrix_height={MATRIX_HEIGHT} matrix_bit_depth={MATRIX_BIT_DEPTH} matrix_color_order={MATRIX_COLOR_ORDER}"
)

# LOCAL VARS
client = None

# STATIC RESOURCES
# logger("loading static resources")
# font_bitocra = bitmap_font.load_font("/bitocra7.bdf")

# RGB MATRIX
logger("configuring rgb matrix")
matrix = Matrix(
    width=MATRIX_WIDTH,
    height=MATRIX_HEIGHT,
    bit_depth=MATRIX_BIT_DEPTH,
    color_order=MATRIX_COLOR_ORDER,
)
accelerometer = LIS3DH_I2C(I2C(board.SCL, board.SDA), address=0x19)
_ = accelerometer.acceleration  # drain startup readings

# SPLASH
splash_group = Group()
splash_group.append(Label(x=1, y=4, font=FONT, text="Wideboy Jr", color=0x220022))

# DISPLAY / FRAMEBUFFER
logger("configuring display/framebuffer")
display = matrix.display
display.rotation = matrix_rotation(accelerometer)
display.show(splash_group)
del accelerometer

# NETWORKING
logger("configuring networking")
network = Network(status_neopixel=None, debug=DEBUG)
network.connect()
mac = network._wifi.esp.MAC_address
host_id = "{:02x}{:02x}{:02x}{:02x}".format(mac[0], mac[1], mac[2], mac[3])
requests.set_socket(socket, network._wifi.esp)
logger(f"network: host_id={host_id}")

# SCREEN
root_group = Group()
label_test = Label(x=1, y=4, font=FONT, text="Wideboy Jr", color=0x220022)
root_group.append(label_test)


# DRAW
def draw(state):
    global label_test
    label_test.text = str(state["frame"])
    logger(f"draw: state={state}")


# STATE
state = dict(frame=0)


# APP STARTUP
def run():
    global state
    gc.collect()
    logger("Start Event Loop")
    display.show(root_group)
    while True:
        gc.collect()
        try:
            draw(state)
            state["frame"] += 1
        except Exception as e:
            print("EXCEPTION", e)


# STARTUP
run()
