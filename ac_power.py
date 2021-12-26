#! /usr/bin/python

import serial
import glob
import struct
import time
import sys
from math import log10

serialPorts = glob.glob('/dev/ttyUSB*')

if len(serialPorts)==0 :
    print "Unable to find any serial devices"
    sys.exit()
if len(serialPorts)>1 :
    print "More than one serial device detected"

ac_port = serial.Serial(serialPorts[0], baudrate=9600, timeout=1)

out_file = open("solar.csv", 'wa')
out_file.write("time, voltage, current, power, energy, frequency, pwr_fctr\n")

def crc16(data) :
    crc = 0xFFFF
    for d in data[:-2] :
        crc ^= d
        for i in range(8) :
            if crc&0x0001 : crc ^= 0xA001<<1
            crc >>= 1
    return [crc&0xFF, crc>>8]

request = bytearray(8)
request[0] = 0x01       # device address 1
request[1] = 0x04       # read input registers
request[2] = 0x00       # starting with register 0 - MSB
request[3] = 0x00       #  LSB
request[4] = 0x00       # read 10 registers - MSB
request[5] = 0x0A       #  LSB
#print crc16(request)
request[6:8] = crc16(request)

from optparse import OptionParser
parser = OptionParser(usage="%prog [options]")
parser.add_option("-m", "--meter", action="store_true", dest="meter", default=False)
parser.add_option("-d", "--dump", action="store_true", dest="dump", default=False)
parser.add_option("-l", "--log", action="store_true", dest="log", default=False)
parser.add_option("-r", "--raw", action="store_true", dest="raw", default=False)
(options, leftover) = parser.parse_args()

peak = 0.0
scale = 50
while True :
    ac_port.write(request)

    response = ac_port.read(25)
    if len(response)>=5 :
        if map(ord,response[0:3])==[1,4,20] :
            if map(ord,response[-2:]) == crc16(map(ord,response)) :
                msg = struct.unpack('>3B11H',response)
                if options.raw :
                    print msg

                voltage   =  msg[3] * 0.1 * 2
                current   = (msg[5]*0x10000 + msg[4]) * 0.001
                power     = (msg[7]*0x10000 + msg[6]) * 0.1 * 2
                energy    = (msg[9]*0x10000 + msg[8]) * 1 * 2
                frequency =  msg[10] * 0.1
                pwr_fctr  =  msg[11] * 0.01

                if options.dump :
                    print "voltage = ", voltage
                    print "current = ", current 
                    print "power = ", power 
                    print "energy = ", energy 
                    print "frequency = ", frequency 
                    print "pwr_fctr = ", pwr_fctr 
                    print
                if options.meter :
                    if power < 63 :
                        size = 5
                    else :
                        size = int((log10(power)-1.7)*50)
                        if size > 100 :
                            scale = size/(log10(power)-1.7)
                    bar = '#'*(size) + ' '*(100-size)
                    if size > peak :
                        peak = size
                    else :
                        peak *= 0.99
                    if bar[int(peak)] != '#' :
                        bar = bar[:int(peak)] + '|' + bar[int(peak)+1:]
                    print '%5d '%power + bar[5:] + '\r',
                    sys.stdout.flush()
                     
                if options.log :
                        # ISO time format with UTC offset
                    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S+00:00",time.gmtime())
                    out_file.write(timestamp+",%f,%f,%f,%f,%f,%f\n" %
                            (voltage, current, power, energy, frequency,pwr_fctr))
                    out_file.flush()

                time.sleep(0.5)

            else :
                print "Response has a bad CRC"
        else :
            print "Unknown valid message"
    else :
        print "Unknown response"

