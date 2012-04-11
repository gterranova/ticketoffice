#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Tiny HTTP server supporting threading CGI.
"""

import sys  
import cgi, os, zlib

import cgitb
cgitb.enable()

import traceback
import urllib
import BaseHTTPServer
import CGIHTTPServer

import SocketServer

__version__ = "$Revision$"

import monitor
monitor.start(interval=1.0)

DOCUMENT_ROOT = "/www"

import re
REWRITE_RULES = [('^/framework(/)?', r'/cgi-bin/photos.cgi?path=/')]


class HTTPRequestHandler(CGIHTTPServer.CGIHTTPRequestHandler):

    use_favicon = True
    
    def is_executable(self, path):
        return True

    def do_POST(self):
        env = {}
        env['REQUEST_URI'] = self.path[:]
        os.environ.update(env)
        
        for (src, dst) in REWRITE_RULES:
            p = re.compile(src, re.VERBOSE)
            if p.match(self.path):
                self.path = self.path.replace('?', '&')
                self.path = p.sub(dst,self.path)
                break
        
        return CGIHTTPServer.CGIHTTPRequestHandler.do_POST(self)

    def do_GET(self):
        env = {}
        env['REQUEST_URI'] = self.path[:]
        os.environ.update(env)
        
        for (src, dst) in REWRITE_RULES:
            p = re.compile(src, re.VERBOSE)
            if p.match(self.path):
                self.path = self.path.replace('?', '&')
                self.path = p.sub(dst,self.path)
                break
        
        if self.use_favicon and self.path == '/favicon.ico':
            self.send_response(200)
            self.send_header("Content-type", 'image/x-icon')
            self.send_header("Content-Length", len(favicon))
            self.end_headers()
            self.wfile.write(favicon)
            return
        return CGIHTTPServer.CGIHTTPRequestHandler.do_GET(self)

    def translate_path(self, path):
        path = DOCUMENT_ROOT + path
        return CGIHTTPServer.CGIHTTPRequestHandler.translate_path(self, path)
        
    def run_cgi(self):
        """Execute a CGI script."""
        path = self.path
        dir, rest = self.cgi_info

        i = path.find('/', len(dir) + 1)
        while i >= 0:
            nextdir = path[:i]
            nextrest = path[i+1:]

            scriptdir = self.translate_path(nextdir)
            if os.path.isdir(scriptdir):
                dir, rest = nextdir, nextrest
                i = path.find('/', len(dir) + 1)
            else:
                break

        # find an explicit query string, if present.
        i = rest.rfind('?')
        if i >= 0:
            rest, query = rest[:i], rest[i+1:]
        else:
            query = ''

        # dissect the part after the directory name into a script name &
        # a possible additional path, to be stored in PATH_INFO.
        i = rest.find('/')
        if i >= 0:
            script, rest = rest[:i], rest[i:]
        else:
            script, rest = rest, ''

        scriptname = dir + '/' + script
        scriptfile = self.translate_path(scriptname)
        
        if not os.path.exists(scriptfile):
            self.send_error(404, "No such CGI script (%r)" % scriptname)
            return
        if not os.path.isfile(scriptfile):
            self.send_error(403, "CGI script is not a plain file (%r)" %
                            scriptname)
            return
        ispy = self.is_python(scriptname)
        if not ispy:
            if not (self.have_fork or self.have_popen2 or self.have_popen3):
                self.send_error(403, "CGI script is not a Python script (%r)" %
                                scriptname)
                return
            if not self.is_executable(scriptfile):
                self.send_error(403, "CGI script is not executable (%r)" %
                                scriptname)
                return

        # Reference: http://hoohoo.ncsa.uiuc.edu/cgi/env.html
        # XXX Much of the following could be prepared ahead of time!
        env = {}
        env['SERVER_SOFTWARE'] = self.version_string()
        env['SERVER_NAME'] = "localhost" # self.server.server_name
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PROTOCOL'] = self.protocol_version
        env['SERVER_PORT'] = str(self.server.server_port)
        env['REQUEST_METHOD'] = self.command
        uqrest = urllib.unquote(rest)
        env['PATH_INFO'] = uqrest
        env['PATH_TRANSLATED'] = self.translate_path(uqrest)
        env['DOCUMENT_ROOT'] =  env['PATH_TRANSLATED'] + os.sep
        env['SCRIPT_FILENAME'] = env['PATH_TRANSLATED'] + scriptname
        env['SCRIPT_NAME'] = scriptname
        if query:
            env['QUERY_STRING'] = query
        host = self.address_string()
        if host != self.client_address[0]:
            env['REMOTE_HOST'] = host
        env['REMOTE_ADDR'] = self.client_address[0]
        authorization = self.headers.getheader("authorization")
        if authorization:
            authorization = authorization.split()
            if len(authorization) == 2:
                import base64, binascii
                env['AUTH_TYPE'] = authorization[0]
                if authorization[0].lower() == "basic":
                    try:
                        authorization = base64.decodestring(authorization[1])
                    except binascii.Error:
                        pass
                    else:
                        authorization = authorization.split(':')
                        if len(authorization) == 2:
                            env['REMOTE_USER'] = authorization[0]
        # XXX REMOTE_IDENT
        if self.headers.typeheader is None:
            env['CONTENT_TYPE'] = self.headers.type
        else:
            env['CONTENT_TYPE'] = self.headers.typeheader
        length = self.headers.getheader('content-length')
        if length:
            env['CONTENT_LENGTH'] = length
        accept = []
        for line in self.headers.getallmatchingheaders('accept'):
            if line[:1] in "\t\n\r ":
                accept.append(line.strip())
            else:
                accept = accept + line[7:].split(',')
        env['HTTP_ACCEPT'] = ','.join(accept)
        ua = self.headers.getheader('user-agent')
        if ua:
            env['HTTP_USER_AGENT'] = ua
        co = filter(None, self.headers.getheaders('cookie'))
        if co:
            env['HTTP_COOKIE'] = ', '.join(co)
        # XXX Other HTTP_* headers
        # Since we're setting the env in the parent, provide empty
        # values to override previously set values
        for k in ('QUERY_STRING', 'REMOTE_HOST', 'CONTENT_LENGTH',
                  'HTTP_USER_AGENT', 'HTTP_COOKIE'):
            env.setdefault(k, "")
        os.environ.update(env)

        self.send_response(200, "Script output follows")

        decoded_query = query.replace('+', ' ')
        
        if 1:
            # Other O.S. -- execute script in this process
            save_argv = sys.argv
            save_stdin = sys.stdin
            save_stdout = sys.stdout
            save_stderr = sys.stderr
            try:
                save_cwd = os.getcwd()
                try:
                    sys.argv = [scriptfile]
                    if '=' not in decoded_query:
                        sys.argv.append(decoded_query)
                    sys.stdout = self.wfile
                    sys.stdin = self.rfile
                    execfile(scriptfile, {"__name__": "__main__", "__file__": scriptfile})
                except:
                    print cgitb.html(sys.exc_info())
##                    print "<html><a name='exception'></a><pre>\n"
##                    traceback.print_exc(file=self.wfile)
##                    print "</pre><script>\nwindow.location.href = '#exception';\n</script></html>"                    
                finally:
                    sys.argv = save_argv
                    sys.stdin = save_stdin
                    sys.stdout = save_stdout
                    sys.stderr = save_stderr
                    os.chdir(save_cwd)
            except SystemExit, sts:
                self.log_error("CGI script exit status %s", str(sts))
            else:
##                self.log_message("CGI script exited OK")
                pass
        

favicon = zlib.decompress(
'x\x9c\xb5\x93\xcdN\xdb@\x14\x85\x07\x95\x07\xc8\x8amYv\xc9#\xe4\x11x\x04\x96}'
'\x8c\x88\x1dl\xa0\x9b\xb6A\xa2)\x0bVTB\xa9"\xa5?*I\x16\xad"\x84d\x84DE\x93'
'\x14;v\xc01M\xe2$\x988\xb1l\x9d\xde;v\\\x03\x89TU\xea\xb5N\xe4\xb9\x9a\xef'
'\x1c\xcfO\x84X\xa0\'\x95\x12\xf4\xbb,\x9e/\n\xb1$\x84xF\xa2\x16u\xc2>WzQ\xfc'
'\xf7\xca\xad\xafo\x91T\xd2\x1ai\xe5\x1fx[\xf9\xf4\x01\xc57\xbb\xd8\xdf\xd8'
'\x00\x8d\x11\xf9\x95\x12\xda\x9a\xc3\xae\xe5_\xbdDpk\x03\xc3\xaeT\xd0\xb3\xd0'
'>?\x83Z\xfd\x86Z\xa5\x84\x1fG_\xa4\xe7\x1c^\xa9W\xbfJ\xfe\xb4\xf0\x0e^\xdb'
'\x88}0 \xafA\x0f\xa3+c&O\xbd\xf4\xc1\xf6\xb6d\x9d\xc6\x05\xdcVSz\xb0x\x1c\x10'
'\x0fo\x02\xc7\xd0\xe7\xf1%\xe5\xf3\xc78\xdb\xf9Y\x93\x1eI\x1f\xf8>\xfa\xb5'
'\x8bG<\x8dW\x0f^\x84\xd9\xee\xb5~\x8f\xe1w\xaf{\x83\x80\xb2\xbd\xe1\x10\x83'
'\x88\'\xa5\x12\xbcZ?9\x8e\xb3%\xd3\xeb`\xd4\xd2\xffdS\xb9\x96\x89!}W!\xfb\x9a'
'\xf9t\xc4f\x8aos\x92\x9dtn\xe0\xe8Z\xcc\xc8=\xec\xf7d6\x97\xa3]\xc2Q\x1b(\xec'
'd\x99_\x8dx\xd4\x15%\xce\x96\xf9\xbf\xacP\xd1:\xfc\xf1\x18\xbe\xeb\xe2\xaey'
'\x89;]\xc5\xf1\xfb<\xf3\x99\xe9\x99\xefon\xa2\xdb6\xe5\x1c\xbb^\x8b}FV\x1b'
'\x9es+\xb3\xbd\x81M\xeb\xd1\xe0^5\xf1\xbd|\xc4\xfca\xf2\xde\xf0w\x9cW\xabr.'
'\xe7\xd9\x8dFx\x0e\xa6){\x93\x8e\x85\xf1\xb5\x81\x89\xd9\x82\xa1\x9c\xc8;\xf9'
'\xe0\x0cV\xb8W\xdc\xdb\x83\xa9i\xb1O@g\xa6T*\xd3=O\xeaP\xcc(^\x17\xfb\xe4\xb3'
'Y\xc9\xb1\x17{N\xf7\xfbo\x8b\xf7\x97\x94\xe3;\xcd\xff)\xd2\xf2\xacy\xa0\x9b'
'\xd4g=\x11B\x8bT\x8e\x94Y\x08%\x12\xe2q\x99\xd4\x7f*\x84O\xfa\r\xb5\x916R'
)

#class HTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
class HTTPServer(BaseHTTPServer.HTTPServer):
    pass

def test(HandlerClass=HTTPRequestHandler, ServerClass=HTTPServer, port=8000):
    server_address = ('', port)
    httpd = ServerClass(server_address, HandlerClass)
    sa = httpd.socket.getsockname()
    print "Serving HTTP on", sa[0], "port", sa[1], "..."
    httpd.serve_forever()

if __name__ == '__main__':
    test()
