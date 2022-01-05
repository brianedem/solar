# solar_adc.py

# This library provides access to either the AD7705 or ADS1256.
# The AD7705 can use the standard Python spidev library as the device chip selects
# are wired to the pins 24 and 26 of the head, per PCI standard
# The ADS1256 has its CS connected to pin 15 while the DAC8532's is connected to pin 16
# The ADS1256 also requres a ~8us pause in the serial clock after the command before
# clocking out the data

import time
import spidev
import RPi.GPIO as GPIO

reg_size = (1,1,1,2,1,None,3,3)

REG = {
        'COMM' : 0,
        'SETUP' : 1,
        'CLOCK' : 2,
        'DATA' : 3,
        'TEST' : 5,
        'OFFSET' : 6,
        'GAIN' : 7,
        }

# COMM Reg:
DRDY_N = 0x80
READ    = 0x08
WRITE   = 0x00

# SETUP Reg:
SELF_CAL = 0x40
GAIN1    = 0x00
GAIN2    = 0x08
GAIN4    = 0x10
GAIN8    = 0x18
GAIN16   = 0x20
GAIN32   = 0x28
GAIN64   = 0x30
GAIN128  = 0x38
UNIPOLAR = 0x04
BIPOLAR  = 0x00
BUF      = 0x02
UNBUF    = 0x00
FSYNC    = 0x01

# CLOCK Reg:
CLKDIV   = 0x08
CLK     = 0x04
FS50    = 0x00
FS60    = 0x01
FS250   = 0x02
FS500   = 0x03

class adc :
    def __init__(self, bus, device) :

            # open SPI connection
        self.adc = spidev.SpiDev()
        self.adc.open(bus, device)

            # Set SPI speed and mode
        self.adc.max_speed_hz = 500000
        self.adc.mode = 3

            # device needs to be reset for proper operation - using GPIO25
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(25, GPIO.OUT)
        GPIO.output(25, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(25, GPIO.HIGH)
        GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # default ADC SETUP values
        self.initialized = False
        self.channel = 0
        self.gain = [GAIN1,GAIN1]
        self.unipolar = [BIPOLAR,BIPOLAR]
        self.buf_en = [UNBUF,UNBUF]

            # set clock input divide by 2, 2.4576MHz
        self.write_reg(REG['CLOCK'], CLKDIV | CLK | FS60)

    def read_data(self, channel, gain=None, unipolar=None, buf_en=None) :
        recalibrate = False
        if not self.initialized :
            recalibrate = True
            self.initialized = True
        if self.channel is None or channel!=self.channel :
            recalibarte = True
            self.channel = channel & 0x1
        if gain is not None and gain!=self.gain[channel] :
            recalibrate = True
            self.gain[channel] = gain & 0x7
        if unipolar is not None and unipolar!=self.unipolar[channel] :
            recalibrate = True
            self.unipolar[channel] = unipolar & 0x1
        if buf_en is not None and buf_en!=self.buf_en[channel] :
            recalibrate = True
            self.buf_en[channel] = buf_en & 0x1

        if recalibrate :
            cmd = SELF_CAL | self.gain[channel]<<3 | self.unipolar[channel]<<2 | self.buf_en[channel]<<1
            self.write_reg(REG['SETUP'], cmd)

        for timeout in range(10000) :
            if self.read_reg(REG["COMM"]) & DRDY_N :
                continue
            else :
                break
        #print timeout
        return self.read_reg(REG["DATA"])

    def read_reg(self, reg) :
            # create a message based on the expected response
        msg = [0x0]*(reg_size[reg]+1)
        msg[0] = (reg<<4) | READ | self.channel

            # perform the access
        reply = self.adc.xfer(msg)

            # convert byte sequence to single integer
        value = 0
        for i in msg[1:] :
            value = value<<8 | int(i)

        return value

    def write_reg(self, reg, value) :
        msg = [(reg<<4) | WRITE | self.channel]
        for i in range((reg_size[reg]-1)*8, -8, -8) :
            msg.append((value>>i) & 0xFF)
        reply = self.adc.xfer(msg)
