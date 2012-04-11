#!/usr/bin/python
# -*- coding: utf-8 -*-

import cgi as cgimodule
import cgitb
cgitb.enable()
from datetime import datetime

import os, sys
import cPickle as pickle

import urllib

curdir = os.path.join(os.path.dirname(__file__))
if curdir not in sys.path:
    sys.path.insert(0, curdir)

from admin.tickets import checkin, parse_get_qs

def main():    
    
    params = cgimodule.FieldStorage(keep_blank_values=1)
    params = parse_get_qs(os.environ['QUERY_STRING'], params)
    
        
    args = {}    
    for p in params:
        try:
            args[p] = params[p].value
        except:
            args[p] = [l.value for l in params[p]]

    code = args.get('c', None)
    if code:
        checkin(code)

if __name__ == "__main__":
    main()
