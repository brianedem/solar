import serial
import struct

def crc16(data) :
    crc = 0xFFFF
    for d in data[:-2] :
        crc ^= d
        for i in range(8) :
            if crc&0x0001 : crc ^= 0xA001<<1
            crc >>= 1
    return struct.pack('H',crc)

class ac_meter() :
    def __init__(self, device) :
        self.ac_port = serial.Serial(device, baudrate=9600, timeout=1)

        self.request = bytearray(8)
        self.request[0] = 0x01       # device address 1
        self.request[1] = 0x04       # read input registers
        self.request[2] = 0x00       # starting with register 0 - MSB
        self.request[3] = 0x00       #  LSB
        self.request[4] = 0x00       # read 10 registers - MSB
        self.request[5] = 0x0A       #  LSB
        #print (crc16(request))
        self.request[6:8] = crc16(self.request)

    def read_meter(self) :
        self.ac_port.write(self.request)
        response = self.ac_port.read(25)
        self.msg = response
        if len(response)>=5 :
            if response[0:3]==b'\x01\x04\x14' :
                if response[-2:] == crc16(response) :
                    self.msg = struct.unpack('>3B11H',response)

                    self.voltage   =  self.msg[3] * 0.1 * 2
                    self.current   = (self.msg[5]*0x10000 + self.msg[4]) * 0.001
                    self.power     = (self.msg[7]*0x10000 + self.msg[6]) * 0.1 * 2
                    self.energy    = (self.msg[9]*0x10000 + self.msg[8]) * 1 * 2
                    self.frequency =  self.msg[10] * 0.1
                    self.pwr_fctr  =  self.msg[11] * 0.01

                    return True
        return False
if __name__=='__main__' :
    import glob
    import serial
    #import sys
    #import time

    serialPorts = glob.glob('/dev/ttyUSB*')

    if len(serialPorts)==0 :
        print ("Unable to find any serial devices")
        sys.exit()
    if len(serialPorts)>1 :
        print ("More than one serial device detected")

    ac_meter = ac_meter(serialPorts[0])

    ac_meter.read_meter()

    print (ac_meter.voltage)
