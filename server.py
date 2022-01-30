#! /usr/bin/python3

import os
import time
import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading

HOST_NAME = os.uname() [1]
PORT_NUMBER = 8080

class MyHandler(BaseHTTPRequestHandler):

    def do_HEAD(s) :
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()

    def do_GET(s) :
        (path,sep,opt) = s.path.partition('?')
        options = {}
        for o in opt.split('&') :
            pass    # FIXME

        if path == '/':
            path = '/index.html'
        isStatic = False
        if path.endswith(".html") :
            mimetype = 'text/html'
            isStatic = True
        if path.endswith(".js") :
            mimetype = 'application/javascript'
            isStatic = True
        if path.endswith(".css") :
            mimetype = 'text/css'
            isStatic = True
        if path.endswith(".ico") :
            mimetype = 'image/png'
            isStatic = True
        #print (isStatic, path)
        if isStatic :
            # print(path)
            try:
                filename = os.curdir + '/public' + path
                # print (filename)
                f = open(filename, "rb")
                s.send_response(200)
                s.send_header('Content-type', mimetype)
                s.end_headers()
                s.wfile.write(f.read())
                f.close()
            except IOError:
                s.send_error(404, 'File Not Found: %s' % path)
            return

        if path == '/solar.data' :
            fname = "solar.csv"
            fsize = os.stat(fname).st_size
            dfile = open(fname, "r", encoding="utf-8")
            dfile.seek(fsize-1000)
            data = dfile.readlines()
            fields = data[-1].split(',')
            s.send_response(200)
            s.send_header("Content-type", "application/json")
            s.end_headers()
            json_string = json.dumps({
                "date":         fields[0],
                "voltage":      float(fields[1]),
                "current":      float(fields[2]),
                "power":        float(fields[3]),
                "pf":           float(fields[4]),
                "bus_v":        float(fields[5]),
                "solar_i":      float(fields[6]),
                "discharge_i":  float(fields[8]),
                "charge_i":     float(fields[7]),
                })
            s.wfile.write(bytes(json_string, "utf-8"))
            return
        if path == '/solar.data2' :
            s.send_response(200)
            s.send_header("Content-type", "application/json")
            s.end_headers()
            json_string = json.dumps({
                "power":    power_now,
                "start":    start_iso,
                "min":      minpoints,
                "max":      maxpoints,
                "avg":      avgpoints,
#               "history":  powerpoints
                })
            s.wfile.write(bytes(json_string, "utf-8"))
            return

        s.send_error(404, 'File Not Found: %s' % path)

powerpoints = []
minpoints = []
maxpoints = []
avgpoints = []
power_now = 0
start_iso = ''

def filter_power() :
    global power_now, start_iso
        # open the log file, determine its size
    log_file = "solar.csv"
    pf = open(log_file, "r", encoding="utf-8")
    log_size = os.stat(log_file).st_size

        # determine the UCI time in ISO format 24 hours ago
    now = time.time()
    start = datetime.datetime.utcfromtimestamp(int(now - 24*60*60))
    start -= datetime.timedelta(seconds=start.second) # zero out seconds
    start_iso = start.isoformat() + 'Z'   # convert to string for comparison

        # position the file to slightly more than 24 hours ago
    size_24 = 24*60*60*2*(56+6)    # 9000000
    if log_size < size_24 :
        f_offset = 0
    else :
        f_offset = log_size - size_24
    pf.seek(f_offset)

        # first line read will most likely not start correctly - discard
    line = pf.readline()
    line = pf.readline()
        # there should be a check here to see that we have backed up enough

        # search forward to find an entry that occurs after the starting timestamp
    while line[:19] < start_iso[:19] :
        line = pf.readline()

        # this will parse lines into one minute intervals and add the min/max/avg to an array
    end = start
    timedelta60 = datetime.timedelta(seconds=60)
    while True:
            # advance the endpoint by 60 seconds
        end += timedelta60
            # convert to ISO format
        stop_iso = end.isoformat()
        points = []
            # collect up entries in the 60 second interval
        while line[:19] < stop_iso[:19] :
            power_now = float(line.split(',')[3])
            points.append(power_now)
                # if at the end of the file we need to wait for more data to be appended
            while True :
                line = pf.readline()
                if len(line)>0 : break
                time.sleep(1)
        if len(points)==0 :
                # if the logger is stopped for awhile there may not be any data to log
            entry = (0,0,0) # None
        elif len(points)==1 :
                # or at the edge only one log entry
            entry = (points[0][0], points[0][1], points[0][2])
        else :
                # otherwise we process to fine the min/max/avg
            entry = (min(points),max(points),int(sum(points)//len(points)))

        powerpoints.append(entry)
        minpoints.append((stop_iso,entry[0]))
        maxpoints.append(entry[1])
        avgpoints.append(entry[2])
        if len(powerpoints) > (24*60) :
                # array has reached its max size, trim oldest data
            powerpoints.pop(0)
            minpoints.pop(0)
            maxpoints.pop(0)
            avgpoints.pop(0)
            start += timedelta60
            start_iso = start.isoformat() + 'Z'

if __name__ == '__main__':
    t = threading.Thread(target=filter_power, daemon=True)
    t.start()
    httpd = HTTPServer((HOST_NAME, PORT_NUMBER), MyHandler)
    print (time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt :
        pass
    httpd.server_close()
    print (time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))
