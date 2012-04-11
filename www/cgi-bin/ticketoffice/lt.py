#!/usr/bin/python
# -*- coding: utf-8 -*-

import cgi as cgimodule
import cgitb
cgitb.enable()

import os, sys
import cPickle as pickle

import urllib

curdir = os.path.join(os.path.dirname(__file__))
if curdir not in sys.path:
    sys.path.insert(0, curdir)

from admin.tickets import load, HEADER, FOOTER
    
def main():    

    db = load()
    
    print "Content-type: text/html\n\n"
    print """<!DOCTYPE html>
<html>
<head>
 <meta charset="utf-8">
 <meta name="viewport" content="width=device-width, initial-scale=1">
 <title>Ticket Office</title>
 <link rel="stylesheet" href="http://code.jquery.com/mobile/1.0.1/jquery.mobile-1.0.1.min.css" />
 <link rel="stylesheet" href="../../lab/ticketoffice/css/jqm-docs.css" />
 <script src="http://code.jquery.com/jquery-1.6.4.min.js"></script>
 <script src="http://code.jquery.com/mobile/1.0.1/jquery.mobile-1.0.1.min.js"></script>
<style type="text/css"> 
    table { width:80%; }
    table caption { text-align:left;  }
    table thead th { text-align:center; border-bottom:1px solid #008000; border-top:1px solid #008000; }
    table tfoot th { text-align:right; border-bottom:1px solid #008000; border-top:1px solid #008000; }
    table th, td { text-align:left; padding:3px;} 
</style> 
</head>
<body>
<div id="main" data-role="page">
 <div data-role="content">
 <img src="../../../lab/ticketoffice/images/logo.png" alt="Ticket Office" /><br/>
 <h1>Registered tickets:</h1>"""
    
    print "<table bgcolor=#ffffff><thead><tr>"
    keys = ['id','name','email','payment','trans','date','sent','download','checkin']
    total = len(db['tickets'])
    for key in keys:
        print "<th>%s</th>" % key
    print """</tr></thead><tfoot>
     <tr>
      <th colspan="9">Total %d</th>
     </tr>
    </tfoot><tbody>""" % total
    for t in db['tickets']:
        print "<tr>"
        for key in keys:
            print "<td>%s</td>" % t[key]
        print "</tr>"
    print "</tbody></table>"
    print """  </div>
  <div data-role="footer" class="footer-docs" data-theme="c">
   <p>&copy; 2012 Gianpaolo Terranova</p>
  </div> 
</div>
</body>
</html>
</body></html>
"""
        
    

if __name__ == "__main__":
    main()
