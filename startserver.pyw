import os, sys
from subprocess import Popen, call

filename = 'webserver/pyservergui.pyw'
os.chdir(os.path.dirname(__file__))
PY = "c:\\Python27\\python.exe"
print filename
retcode = 0

while 1:
    try:
        retcode = call([PY, filename], shell=True)
        if retcode == 0:
            break
        else:
            print >>sys.stderr, "Child returned", retcode
    except OSError, e:
        print >>sys.stderr, "Execution failed:", e
    print >>sys.stderr, "\nRestarting..."

##while retcode != 0:
##    proc = Popen([PY, filename], shell=True)
##    retcode = proc.wait()

