#! /usr/bin/python3

import serial
import glob
import struct
import time
import sys
from math import log10
from math import modf
import ac_monitor
import dc_monitor

serialPorts = glob.glob('/dev/ttyUSB*')

if len(serialPorts)==0 :
    print ("Unable to find any serial devices")
    sys.exit()
if len(serialPorts)>1 :
    print ("More than one serial device detected")

ac_meter = ac_monitor.ac_meter(serialPorts[0])

out_file = open("solar.csv", 'a+', 1)   # line  buffering

from optparse import OptionParser
parser = OptionParser(usage="%prog [options]")
parser.add_option("-m", "--meter", action="store_true", dest="meter", default=False)
parser.add_option("-d", "--dump", action="store_true", dest="dump", default=False)
parser.add_option("-l", "--log", action="store_true", dest="log", default=False)
parser.add_option("-r", "--raw", action="store_true", dest="raw", default=False)
(options, leftover) = parser.parse_args()

meter_peak = 0.0
while True :
    #bus_voltage = dc_monitor.vbus()
    bus_voltage = 410

    battery_current = dc_monitor.ibattery()
    battery_current = dc_monitor.ibattery()
    #print (battery_current)
    if battery_current < 0 :
        battery_discharge = -battery_current
        battery_charge = 0.0
    else :
        battery_discharge = 0.0
        battery_charge = battery_current

    solar_current = dc_monitor.isolar()
    solar_current = dc_monitor.isolar()

    if ac_meter.read_meter() :

        if options.raw :
            print (ac_meter.msg)

        if options.dump :
            print ("voltage = ", ac_meter.voltage)
            print ("current = ", ac_meter.current )
            print ("power = ", ac_meter.power )
            print ("pwr_fctr = ", ac_meter.pwr_fctr )
            print ("bus voltage = ", bus_voltage)
            print ("solar_current = ", solar_current)
            print ("bat_charge = ", battery_charge)
            print ("bat_discharge = ", battery_discharge)
            print ()

        if options.log :
                # ISO time format with UTC offset
            ctime = time.time()
            fseconds,iseconds = modf(ctime)
            timestamp = time.strftime("%Y-%m-%dT%H:%M:%S",time.gmtime(ctime))+".%dZ"%int(fseconds*10)
            out_file.write(timestamp+",%.1f,%.3f,%.1f,%.2f,%d,%.2f,%.2f,%.2f\n" % (
                ac_meter.voltage,
                ac_meter.current,
                ac_meter.power,
                ac_meter.pwr_fctr,
                bus_voltage,
                solar_current,
                battery_discharge,
                battery_charge,
                ))

        if options.meter :
                # minimum size is 5 to provide room for value text
            if ac_meter.power < 63 :
                size = 5
            else :
                    # log meter bar, 50-5000W. Difference in logs is 2
                    # log10(50) is ~1.7
                size = int((log10(ac_meter.power)-1.7)*50)

                # create the bar graph
            bar = '#'*(size) + ' '*(100-size)

            if size > meter_peak :
                    # set new meter_peak
                meter_peak = size
            else :
                    # or age
                meter_peak *= 0.99

                # string is indexed by 0..99
            if bar[int(meter_peak)-1] != '#' :
                bar = bar[:int(meter_peak)-1] + '|' + bar[int(meter_peak):]
            print ('%5d '%ac_meter.power + bar[5:] + '\r', end='')
            sys.stdout.flush()

        time.sleep(0.5)

    else :
        print ("Unexpected respose from meter: ", ac_meter.msg)

