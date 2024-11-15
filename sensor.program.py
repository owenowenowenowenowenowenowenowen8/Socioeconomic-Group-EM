# 1. Imports
import time
import board
import adafruit_scd4x
import busio
from digitalio import DigitalInOut, Direction, Pull
from adafruit_pm25.i2c import PM25_I2C
import adafruit_sdcard
import digitalio
import microcontroller
import storage
import random
import displayio
import adafruit_displayio_sh1107
import terminalio
from adafruit_display_text import label
import adafruit_gps


try:
    from i2cdisplaybus import I2CDisplayBus

    # from fourwire import FourWire
except ImportError:
    from displayio import I2CDisplay as I2CDisplayBus


# 2. Defining/addressing functions
## temp/rh/CO2 sensor
i2c_scd4x = board.STEMMA_I2C()
scd4x = adafruit_scd4x.SCD4X(i2c_scd4x)

## air quality sensor
reset_pin = None
i2c_pm = board.STEMMA_I2C()
pm25 = PM25_I2C(i2c_pm, reset_pin)

## SD card
SD_CS = board.SD_CS
cs = digitalio.DigitalInOut(SD_CS)
sdcard = adafruit_sdcard.SDCard(board.SPI(), cs)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")

## GPS
i2c_gps = board.STEMMA_I2C()
gps = adafruit_gps.GPS_GtopI2C(i2c_gps)
gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
gps.send_command(b"PMTK220,1000")


# 3. Initialization functions
scd4x.start_periodic_measurement()

## create file name from random number
random_number = random.getrandbits(32)

file_name = "/sd/"+str(random_number)+".csv"
print(file_name)
with open(file_name, 'x') as f:
    print("datetime", "lat", "long", "n_satellites", "temp_C", "rh", "CO2_ppm", "particles03um", "particles05um", "particles10um", "particles25um", "particles50um", "particles100um", sep =",", file=f)


## set parameters of display
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 128  # Change to 64 if needed
BORDER = 2
ROTATION = 0
## create and address the display
displayio.release_displays()
i2c_display = board.STEMMA_I2C()
display_bus = I2CDisplayBus(i2c_display, device_address=0x3D)

display = adafruit_displayio_sh1107.SH1107(
    display_bus,
    width=DISPLAY_WIDTH,
    height=DISPLAY_HEIGHT,
    rotation=ROTATION,
)

## Create text items
font = terminalio.FONT
color = 0x0000FF
text_row1 = label.Label(font, color=color)
text_row2 = label.Label(font, color=color)
text_row3 = label.Label(font, color=color)
text_row4 = label.Label(font, color=color)

# define temporary variables
var_temp = 0
var_rh = 0
var_CO2 = 0
aqdata_03um = 0
aqdata_05um = 0
aqdata_10um = 0
aqdata_25um = 0
aqdata_50um = 0
aqdata_100um = 0

# 4. Main loop
while True:
    i = 1
    while i < 10:
        gps.update()
        time.sleep(0.1)
        i += 1
        # print(i)
    if not gps.has_fix:
        print("no satellite fix")
    if gps.has_fix:
	    # measure sensors
        if scd4x.data_ready:
            var_temp = scd4x.temperature
            var_rh = scd4x.relative_humidity
            var_CO2 = scd4x.CO2
        aqdata = pm25.read()
        aqdata_03um = aqdata["particles 03um"]
        aqdata_05um = aqdata["particles 05um"]
        aqdata_10um = aqdata["particles 10um"]
        aqdata_25um = aqdata["particles 25um"]
        aqdata_50um = aqdata["particles 50um"]
        aqdata_100um = aqdata["particles 100um"]

        # GPS variables
        gps.update()
        datetime = "{}/{}/{}_{:02}:{:02}:{:02}".format(gps.timestamp_utc.tm_mon,gps.timestamp_utc.tm_mday,gps.timestamp_utc.tm_year,gps.timestamp_utc.tm_hour,gps.timestamp_utc.tm_min,gps.timestamp_utc.tm_sec)
        latitude = "{0:.6f}".format(gps.latitude)
        longitude = "{0:.6f}".format(gps.longitude)
        n_satellites = "{}".format(gps.satellites)

        # Update label for displaying data
        text_row1.text = "sats: {}".format(n_satellites)
        text_row2.text = "T:   {:.1f}".format(var_temp)
        text_row3.text = "CO2: {:.0f}".format(var_CO2)
        text_row4.text = "PM05: {:.0d}".format(aqdata_05um)
        #
        ## setup lines of text on display
        text_area_row1 = label.Label(terminalio.FONT, text=text_row1.text, scale=2)
        text_area_row1.anchor_point = (0.0, 0.0)
        text_area_row1.anchored_position = (0, 0)
        #
        text_area_row2 = label.Label(terminalio.FONT, text=text_row2.text, scale=2)
        text_area_row2.anchor_point = (0.0, 0.3)
        text_area_row2.anchored_position = (0, DISPLAY_HEIGHT/3)
        #
        text_area_row3 = label.Label(terminalio.FONT, text=text_row3.text, scale=2)
        text_area_row3.anchor_point = (0.0, 0.6)
        text_area_row3.anchored_position = (0, 2*DISPLAY_HEIGHT/3)
        #
        text_area_row4 = label.Label(terminalio.FONT, text=text_row4.text, scale=2)
        text_area_row4.anchor_point = (0.0, 1.0)
        text_area_row4.anchored_position = (0, DISPLAY_HEIGHT)
        #
        text_group = displayio.Group()
        text_group.append(text_area_row1)
        text_group.append(text_area_row2)
        text_group.append(text_area_row3)
        text_group.append(text_area_row4)
        #
        display.root_group = text_group
        #
	    # write to file
        with open(file_name, 'a') as f:
            print(datetime, latitude, longitude, n_satellites, "{:.1f}".format(var_temp), "{:.1f}".format(var_rh), var_CO2, aqdata_03um, aqdata_05um, aqdata_10um, aqdata_25um, aqdata_50um, aqdata_100um, sep =",", file=f)
        print(datetime, n_satellites, "{:.1f}".format(var_temp), "{:.1f}".format(var_rh), var_CO2, aqdata_03um, aqdata_05um, aqdata_10um, aqdata_25um, aqdata_50um, aqdata_100um, sep =",")