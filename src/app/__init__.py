import board
import gc
import terminalio
import time
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_requests as requests

# from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes.roundrect import RoundRect
from adafruit_display_text.label import Label
from adafruit_displayio_layout.layouts.grid_layout import GridLayout
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
    TILE_COLS,
    TILE_ROWS,
)

from app.utils import logger, matrix_rotation, get_new_epochs

TILE_WIDTH = MATRIX_WIDTH // TILE_COLS
TILE_HEIGHT = MATRIX_HEIGHT // TILE_ROWS

# Local Classes


class GridGroup(Group):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        super().__init__()


class CellLabel(Label):
    def __init__(self, text, color=0x222222, font=FONT, x=2, y=6):
        super().__init__(x=x, y=y, text=text, color=color, font=font)


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
logger("Configuring RGB Matrix")
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
logger("Configuring Display")
display = matrix.display
display.rotation = matrix_rotation(accelerometer)
display.show(splash_group)
del accelerometer

# NETWORKING
logger("Configuring Networking")
network = Network(status_neopixel=None, debug=DEBUG)
network.connect()
mac = network._wifi.esp.MAC_address
host_id = "{:02x}{:02x}{:02x}{:02x}".format(mac[0], mac[1], mac[2], mac[3])
requests.set_socket(socket, network._wifi.esp)
logger(f"Host ID: {host_id}")

# SCREEN
root_group = Group()

# Layout


layout = GridLayout(
    x=0,
    y=0,
    width=MATRIX_WIDTH,
    height=MATRIX_HEIGHT,
    grid_size=(2, 2),
)
root_group.append(layout)


def build_tile(children, radius=2, background_color=0, outline_color=None):
    group = GridGroup(TILE_WIDTH, TILE_HEIGHT)
    rect = RoundRect(
        x=0,
        y=0,
        width=TILE_WIDTH,
        height=TILE_HEIGHT,
        r=radius,
        fill=background_color,
        outline=outline_color,
    )
    group.append(rect)
    group.append(children)
    return group


# Cells

label_wideboy = CellLabel("WB Jr", 0x222222)
layout.add_content(
    build_tile(label_wideboy, background_color=0x110000),
    grid_position=(0, 0),
    cell_size=(1, 1),
)

label_frame = CellLabel("0", 0x222222)
layout.add_content(
    build_tile(label_frame, background_color=0x000011),
    grid_position=(1, 0),
    cell_size=(1, 1),
)

label_frame_mod_100 = CellLabel("0", 0x222222)
layout.add_content(
    build_tile(label_frame_mod_100, background_color=0x001100),
    grid_position=(0, 1),
    cell_size=(1, 1),
)

label_frame_mod_60 = CellLabel("0", 0x222222)
layout.add_content(
    build_tile(label_frame_mod_60, background_color=0x110011),
    grid_position=(1, 1),
    cell_size=(1, 1),
)


# DRAW
def draw(state):
    global label_frame
    label_frame.text = str(state["frame"])
    label_frame_mod_100.text = str(state["frame"] % 100)
    label_frame_mod_60.text = str(state["frame"] % 60)
    logger(f"Draw: state={state}")


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
