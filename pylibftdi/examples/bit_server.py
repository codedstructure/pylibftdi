"""
bit_server.py - remote HTTP interface to bit-bangged FTDI port
This runs as a web server, connect to port 8008

Change HTTP_PORT for different port number or supply alternate as args[1]

Requires:
 - pylibftdi
"""

import sys
import threading
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
from socketserver import ThreadingMixIn
from pylibftdi import BitBangDevice

HTTP_PORT = 8008


class ThreadingServer(ThreadingMixIn, HTTPServer):
    pass


def get_page():
    port = switch.port
    page = """
<!DOCTYPE html>
<html>
<head>
 <title>%s - pylibftdi</title>
</head>
<body>
<div>
""" % port
    for i in range(8):
        bit = 7 - i
        is_on = port & (1 << bit)
        color = '#00FF00' if is_on else '#FF0000'
        page += """
<fieldset style="background-color: %s; display: inline-block; margin:0px; padding: 8px;">
<form action="" method="post" >
<input type="checkbox" onchange="document.querySelector('[name=bit%d]').value=this.checked; document.forms[%d].submit()" %s />
<input type="hidden" name="bit%d" />
</form>
</fieldset>
""" % (color, bit, i, 'checked="checked"' if is_on else '', bit)
    page += """
</div>
DATA=%s
</body>
</html>
""" % port
    return page


class ReqHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        f = self.send_head()
        if f:
            self.wfile.write(f.read())
            f.close()

    def do_POST(self):
        length = self.headers['content-length']
        nbytes = int(length)
        query = self.rfile.read(nbytes).decode()
        # this is lazy and fragile - assumes only a single
        # query parameter XXX
        if query.startswith('bit'):
            bit = int(query[3])
            value = 1 if query.rsplit('=', 1)[-1] == 'true' else 0
            if value:
                switch.port |= (1 << bit)
            else:
                switch.port &= 255 ^ (1 << bit)

        f = self.send_head()
        if f:
            self.wfile.write(f.read())
            f.close()

    def send_head(self):
        f = BytesIO()
        f.write(get_page().encode())
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f


def runserver(port=HTTP_PORT):
    serveraddr = ('', port)
    srvr = ThreadingServer(serveraddr, ReqHandler)
    srvr.serve_forever()

if __name__ == '__main__':
    switch = BitBangDevice()

    try:
        HTTP_PORT = int(sys.argv[1])
    except (ValueError, TypeError):
        print("Usage: FtdiWebServer [portnumber]")
    except IndexError:
        pass

    t = threading.Thread(target=runserver, args=(HTTP_PORT,))
    t.setDaemon(True)
    t.start()
    print("Webserver running on localhost port %d" % HTTP_PORT)
    time.sleep(0.5)
    retry = 10
    while retry:
        try:
            webbrowser.open('http://localhost:%d' % HTTP_PORT)
        except EnvironmentError:
            time.sleep(1)
            retry -= 1
        else:
            break

    # wait for Ctrl-C
    try:
        while 1:
            time.sleep(100)
    except KeyboardInterrupt:
        pass
