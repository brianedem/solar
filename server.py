#! /usr/bin/python

import os
import time
import BaseHTTPServer
import json

HOST_NAME = os.uname() [1]
PORT_NUMBER = 8080

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_HEAD(s) :
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()

    def do_GET(s) :
        if s.path == '/':
            s.path = '/index.html'
        isStatic = False
        if s.path.endswith(".html") :
            mimetype = 'text/html'
            isStatic = True
        if s.path.endswith(".js") :
            mimetype = 'application/javascript'
            isStatic = True
        if s.path.endswith(".css") :
            mimetype = 'text/css'
            isStatic = True
        if s.path.endswith(".ico") :
            mimetype = 'image/png'
            isStatic = True
        #print isStatic, s.path
        if isStatic :
            # print(s.path)
            try:
                filename = os.curdir + '/public' + s.path
                # print filename
                f = open(filename)
                s.send_response(200)
                s.send_header('Content-type', mimetype)
                s.end_headers()
                s.wfile.write(f.read())
                f.close()
            except IOError:
                s.send_error(404, 'File Not Found: %s' % s.path)
            return

        if s.path == '/solar.data' :
            fname = "solar.csv"
            fsize = os.stat(fname).st_size
            dfile = open(fname)
            dfile.seek(fsize-1000)
            data = dfile.readlines()
            fields = data[-1].split(',')
            s.send_response(200)
            s.send_header("Content-type", "application/json")
            s.end_headers()
            json_string = json.dumps({
                "date":     fields[0],
                "voltage":  float(fields[1]),
                "current":  float(fields[2]),
                "power":    float(fields[3]),
                "energy":   float(fields[4]),
                "freq":     float(fields[5]),
                "pf":       float(fields[6])
                })
            s.wfile.write(json_string)
            return
        s.send_error(404, 'File Not Found: %s' % s.path)

if __name__ == '__main__':
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt :
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)
#time, voltage, current, power, energy, frequency, pwr_fctr
#Thu Dec 23 09:49:02 2021,244.200000,0.848000,191.800000,38644.000000,60.000000,0.930000
