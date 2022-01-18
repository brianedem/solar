import time
import spidev
import RPi.GPIO as GPIO
import struct

REG = {
            "STATUS" : 0,
            "MUX" : 1,
            "ADCON" : 2,
            "DRATE" : 3,
            "IO" : 4,
            "OFC0" : 5,
            "OFC1" : 6,
            "OFC2" : 7,
            "FSC0" : 8,
            "FSC1" : 9,
            "FSC2" : 10,
        }
reg_size = (1,1,1,1,1,3,1,1,3,1,1)

# STATUS Register
ORDER_LEAST = 0x08
ACAL_EN = 0x04
BUFEN   = 0x02
DRDY    = 0x01

# MUX Register
PSEL0 = 0x00
PSEL1 = 0x10
PSEL2 = 0x20
PSEL3 = 0x30
PSEL4 = 0x40
PSEL5 = 0x50
PSEL6 = 0x60
PSEL7 = 0x70
PCOM  = 0x80
NSEL0 = 0x00
NSEL1 = 0x01
NSEL2 = 0x02
NSEL3 = 0x03
NSEL4 = 0x04
NSEL5 = 0x05
NSEL6 = 0x06
NSEL7 = 0x07
NCOM  = 0x08

# ADCON Register
SDCS_OFF = 0x00
SDCS_P5  = 0x08
SDCS_2   = 0x10
SDCS_10  = 0x18

PGA1  = 0x00
PGA2  = 0x01
PGA4  = 0x02
PGA8  = 0x03
PGA16 = 0x04
PGA32 = 0x05
PGA64 = 0x06

# DRATE Register
DP2p5   = 0x03
DP5     = 0x13
DP10    = 0x23
DP15    = 0x33
DP25    = 0x43
DP30    = 0x53
DP50    = 0x63
DP60    = 0x72
DP100   = 0x82
DP500   = 0x92
DP1000  = 0xA0
DP2000  = 0xB0
DP3750  = 0xC0
DP7500  = 0xD0
DP15M   = 0xE0
DP20M   = 0xF0

# GPIO Registers
DIR3_IN = 0x80
DIR2_IN = 0x40
DIR3_IN = 0x20
DIR0_IN = 0x10
DIR3_STAT = 0x08
DIR2_STAT = 0x04
DIR1_STAT = 0x02
DIR0_STAT = 0x01

# ADC Commands
WAKEUP      = 0x00
RDATA       = 0x01
RDATAC      = 0x03
SDATAC      = 0x0F
RREG        = 0x10
WREG        = 0x50
SELFCAL     = 0xF0
SELFOCAL    = 0xF1
SELFGCAL    = 0xF2
SYSOCAL     = 0xF3
SYSGCAL     = 0xF4
SYNC        = 0xFC
STANDBY     = 0xFD
RESET       = 0xFE
#WAKEUP      = 0xFF

# GPIO Mapping
PIN_DRDY = 17
PIN_RESET = 18
PIN_CS = 22
PIN_SYNCN = 27

# ADC voltage reference
vref = 2.5

class adc :
    def __init__(self, bus, device) :

            # open SPI connection
        self.adc = spidev.SpiDev()
        self.adc.open(bus, device)

            # Set SPI speed and mode
        self.adc.max_speed_hz = 500000
#       self.adc.mode = 1
        self.adc.mode = 1
        self.adc.no_cs = True

            # configure GPIO for the device
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIN_DRDY, GPIO.IN)
        GPIO.setup(PIN_RESET, GPIO.OUT)
        GPIO.setup(PIN_CS, GPIO.OUT)
        GPIO.setup(PIN_SYNCN, GPIO.OUT)
        GPIO.output(PIN_RESET, GPIO.LOW)
        GPIO.output(PIN_CS, GPIO.HIGH)
        GPIO.output(PIN_SYNCN, GPIO.HIGH)

            # release ADC pin reset
        GPIO.output(PIN_RESET, GPIO.HIGH)
#       time.sleep(0.01)

            # initial configuration of ADC
#       self.cmd(WAKEUP)
#       self.cmd(RESET)

            # registers initially don't work - wait until status is non-zero
        while self.read_reg(REG["STATUS"]) == 0 :
            pass

        self.write_reg(REG["DRATE"], DP1000)    # sampling rate
        self.write_reg(REG["STATUS"], BUFEN)
#       self.write_reg(REG["STATUS"], ACAL_EN | BUFEN)
        self.cmd(SELFCAL)   # autocalibration complicates configuration changes
        self.wait_drdy()

            # defaut ADC setup - changing these values require recalibration
        self.buf_en = 0
        self.gain = PGA1
        self.channel = PSEL0 | NSEL1

            # channel_map: (buf_en, gain)
        self.channel_config = {}

    def wait_drdy(self) :
        while GPIO.input(PIN_DRDY) :
            pass

    def cmd(self, command) :

        msg = [command,]
        GPIO.output(PIN_CS, GPIO.LOW)
        #print "write", msg
        self.adc.xfer(msg)
        GPIO.output(PIN_CS, GPIO.HIGH)

    def write_reg(self, reg, value) :
        msg = [WREG|reg, reg_size[reg]-1]
        for i in range((reg_size[reg]-1)*8, -8, -8) :
            msg.append((value>>i) & 0xFF)
        GPIO.output(PIN_CS, GPIO.LOW)
        #print "write", msg
        self.adc.xfer(msg)
        GPIO.output(PIN_CS, GPIO.HIGH)

    def read_reg(self, reg) :
        GPIO.output(PIN_CS, GPIO.LOW)
        msg = [RREG|reg, reg_size[reg]-1]
            # reading requires a 50 clock delay between command and data
        self.adc.xfer2(msg, self.adc.max_speed_hz, 8, 8)
        msg = [0x00]*reg_size[reg]
        reply = self.adc.xfer(msg)
        GPIO.output(PIN_CS, GPIO.HIGH)
        value = 0
        for i in msg :
            value = value<<8 | int(i)
        return value

    def read_data(self, channel, gain=None, unipolar=None, buf_en=None) :
            # if channel has not be used yet set up a default configuration
        self.cmd(SYNC)
        if channel not in self.channel_config :
            if gain is None :
                gain = PGA1
            if buf_en is None :
                buf_en = 0
            self.channel_config[channel] = [buf_en, gain]

            # fill in unspecified values
        if buf_en is None :
            buf_en = self.channel_config[channel][0]
        elif buf_en != False :
            buf_en = BUFEN
            self.channel_config[channel][0] = buf_en
        else :
            self.channel_config[channel][0] = 0

        if gain is None :
            gain = self.channel_config[channel][1]
        else :
            self.channel_config[channel][1] = gain

            # update hardware is configuration has changed
        need_cal = 0
        if channel != self.channel :
            self.write_reg(REG["MUX"], channel)

                # generate a SYNC to restart conversion
            #GPIO.output(PIN_SYNCN, GPIO.LOW)
            #print "generating sync", hex(channel)
            #self.cmd(SYNC)
            #self.cmd(WAKEUP)
        if buf_en != self.buf_en :
            self.write_reg(REG["STATUS"], ACAL_EN | buf_en)
            self.buf_en = buf_en
            need_cal = 1
        if gain != self.gain :
            self.write_reg(REG["ADCON"], gain)
            self.gain = gain
            need_cal = 1

            # if MUX changed release SYNC to start conversion
            # other configuration changes will cause internal SYNC generation
        #GPIO.output(PIN_SYNCN, GPIO.HIGH)
        if need_cal :
#           #print "calibrating"
            self.cmd(SELFCAL)
        else :
            self.cmd(WAKEUP)

            # wait for data ready
        while GPIO.input(PIN_DRDY) :
            pass

            # read the 3 bytes of data (24-bit)
        GPIO.output(PIN_CS, GPIO.LOW)
        msg = [RDATA, ]
            # reading requires a 50 clock delay between command and data
        self.adc.xfer2(msg, self.adc.max_speed_hz, 8, 8)
        msg = [0x00]*3
        reply = self.adc.xfer(msg)
        GPIO.output(PIN_CS, GPIO.HIGH)

            # convert the 3-byte value to 24-bit
        if reply[0] & 0x80 :
            (value,) = struct.unpack(">l",'\xFF'+''.join(map(chr,reply)))
        else :
            (value,) = struct.unpack(">l",'\x00'+''.join(map(chr,reply)))
#       value = 0
#       for i in reply :
#           value = value<<8 | int(i)
        return value * 2.0 * vref / 2**23
