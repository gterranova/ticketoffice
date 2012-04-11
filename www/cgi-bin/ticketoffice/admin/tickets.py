#!/usr/bin/python
# -*- coding: utf-8 -*-

import cgi as cgimodule
import cgitb
cgitb.enable()

from datetime import datetime
import os, sys
import cPickle as pickle

import urllib, urllib2
import zlib

from base64 import b64encode
import math

def randStr(n):
    return b64encode(os.urandom(int(math.ceil(0.75*n))),'Az')[:n]

opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
urllib2.install_opener(opener)

curdir = os.path.join(os.path.dirname(__file__))
TICKET_FILE=os.path.join(curdir,'..',"tickets.dat")

site_packages = os.path.join(curdir, '..','..', 'site_packages')
pyfpdfpath = os.path.join(curdir, '..', '..', 'site_packages','pyfpdf')

if site_packages not in sys.path:
    sys.path.insert(0, site_packages)
if pyfpdfpath not in sys.path:
    sys.path.insert(0, pyfpdfpath)

from pyfpdf.fpdf import FPDF
from pyfpdf.html import HTML2FPDF

class MyTicket(FPDF):
    def __init__(self,t):
        #First page
        self.t = t
        FPDF.__init__(self)
        
    def generate(self):
        data = urllib.urlencode({'cht' : 'qr','chs':'300x300',
                                 'chl': checkinurl(self.t)
                                 })

        if os.path.exists(os.path.join(curdir,'..','qrcode.png')):
            os.unlink(os.path.join(curdir,'..','qrcode.png'))
        qrcode = _openUrl('https://chart.googleapis.com/chart',data=data)
        f = open(os.path.join(curdir,'..','qrcode.png'),'wb')
        f.write(qrcode)
        f.close()        
                                
        self.add_page()
        self.output(pdffile(self.t),'F')
        os.unlink(os.path.join(curdir,'..','qrcode.png'))
        
    def header(self):
        self.image(os.path.join(curdir,'..','logo.png'),0,10,120)
        self.image(os.path.join(curdir,'..','qrcode.png'),115,38,50)
        self.line(10,2,200,2)        
        self.set_font('Arial','B',15)
        self.cell(110)
        self.cell(40,18,'Ticket %(id)s/%(pdfcode)s' % self.t,0,0,'L')
        self.ln(10)
        self.set_font('Arial','B',8)
        self.cell(110)
        self.cell(1,10,"Legend 54, viale Enrico Fermi 98 (MM Affori), Milano.",0,0,'TL')
        self.ln(4)
        self.cell(110)
        self.cell(1,10,"February 25th, 2012 from 9pm.",0,0,'TL')
        self.ln(4)
        self.cell(110)
        self.cell(1,10,'Name: %(name)s %(email)s' % self.t,0,0,'TL')
        self.ln(4)
        self.cell(110)
        self.cell(1,10,'Payment on %(date)s via %(payment)s confirmed.' % self.t,0,0,'TL')
        self.line(10,95,200,95)
            
    def footer(self):
        #self.set_y(-15)
        #self.set_font('Arial','I',8)
        #txt = 'Page %s of %s' % (self.page_no(), self.alias_nb_pages())
        #self.cell(0,10,txt,0,0,'C')
        pass
        
def pdfurl(t):
    return "http://www.terranovanet.it/cgi-bin/ticketoffice/dl.py?c=%(pdfcode)s" % t

def internal_pdfurl(t):
    return "http://www.terranovanet.it/cgi-bin/ticketoffice/admin/tickets.py?c=%(pdfcode)s&q=showpdf" % t

def checkinurl(t):
    return "http://www.terranovanet.it/cgi-bin/ticketoffice/ck.py?c=%(pdfcode)s" % t

def pdffile(t):
    return os.path.join(curdir,'..',"tickets","ticket%(id)s.pdf" % t)
                        
def find(n):
    db = load()
    for t in db['tickets']:
        if t['id'] == int(n):
            return t
    return None

def findcode(n):
    db = load()
    for t in db['tickets']:
        if t['pdfcode'] == n:
            return t
    return None

def showpdf(n, updatedb=False):
    db = load()
    for t in db['tickets']:
        if t['pdfcode'] == n:
            if updatedb:
                t['download'] = datetime.now().strftime("%d-%m-%Y %H:%M")
                save(db)
            f = open (pdffile(t), "rb")
            #s = f.read()
            #length = len(s)
            #f.close()
            sys.stdout.write("Content-type: application/pdf\n")
            sys.stdout.write("Content-Disposition: attachment; filename=\"ticket.pdf\"\n\n" )
            #print "Content-Length: %d\n\n" % (length + length)
            while True:
                buf =f.read(1024)
                if not buf: break
                sys.stdout.write(buf)
            f.close()
            return True
    return False

def insert(t):
    db = load()
    db['count'] = t['id'] = db['count'] + 1
    t['sent'] = False
    t['download'] = False
    t['checkin'] = False
    t['pdfcode'] = randStr(5)
    db['tickets'].append(t)
    myticket = MyTicket(t)
    myticket.generate()    
    save(db)

def delete(n):
    db = load()
    l = db['tickets'][:]
    for t in l:
        if t['id'] == int(n):
            db['tickets'].remove(t)
            save(db)
            os.unlink(pdffile(t))
            return True
    return False

def load():
    if not os.path.exists(TICKET_FILE):
        return {'count': 0, 'checkin': 'Off', 'tickets': []}
    return pickle.load( open( TICKET_FILE, "rb" ) )

def save(t):
    pickle.dump( t, open( TICKET_FILE, "wb" ) )
    pass

def showlist(unsent=0,undownloaded=0,unchecked=0):
    db = load()
    output = """<div data-role="controlgroup" data-type="horizontal">
			<a href="?q=showlist" data-role="button">All</a>
			<a href="?q=showlist&unsent=1" data-role="button">Unsent</a>
			<a href="?q=showlist&undownloaded=1" data-role="button">Undownloaded</a>
			<a href="?q=showlist&unchecked=1" data-role="button">Unchecked</a>						
		</div>"""
    output += """<ul data-role="listview" data-inset="true" data-filter="true" data-theme="d" data-dividertheme="b">
    <li data-role='list-divider'>Ticket list (%d)</li>""" % len(db['tickets'])
    for t in db['tickets']:
        if unsent == 1:
            if t['sent'] != False:
                continue
        if undownloaded == 1:
            if t['download'] != False:
                continue
        if unchecked == 1:
            if t['checkin'] != False:
                continue
            
        output += "<li><a href='?id=%(id)s&q=showticket' data-transition='slideup'><h3>%(name)s (id: %(id)s/%(pdfcode)s)</h3><p>%(email)s</p></a></li>" % t
        output += "</li>"
    output += "</ul>"
    return output

def showticket(n):
    t = find(n)
    if not t:
        return """<ul data-role="listview" data-inset="true" data-theme="d" data-dividertheme="b">
    <li data-role='list-divider'>Ticket id:%(n)s</li><li>The ticket do not exists!</li></ul>""" % n
    
    output = """<ul data-role="listview" data-inset="true" data-theme="d" data-dividertheme="b">
    <li data-role='list-divider'>Ticket id:%(id)s</li>""" % t
    for field in ['name','email','sent','download','checkin']:
        output += "<li><p><b>%s:</b> %s</p></li>" % (field, t[field])
    output += "<li data-role='list-divider' data-theme='a' data-divider-theme='a'>Payment info:</li>"
    for field in ['payment','trans','date']:
        output += "<li><p><b>%s:</b> %s</p></li>" % (field, t[field])
    output += """<li><fieldset class="ui-grid-b"><div class="ui-block-a"><a data-role='button' rel='external' href='%s' target='_blank'>View PDF</a></div>
<div class="ui-block-b"><a data-role='button' href='?id=%s&q=email'>Send email</a></div>
<div class="ui-block-c"><a class="confirmLink" data-role='button' href='?id=%s&q=delete'>Delete</a></div></fieldset></li>""" % (internal_pdfurl(t), t['id'], t['id'])
    output += """</ul>
<script>
   $(".confirmLink").bind('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    var targetUrl = $(this).attr("href");

    var answer = confirm("This operation will be irreversible, so please think twice before you delete a ticket!\\nAre you sure you know what you are doing?");
    if (answer) {
      window.location.href = targetUrl;
    }
    return false;
  });
</script>
"""
    return output

def sendmsg(n):
    t = find(n)
    if not t:
        return """<ul data-role="listview" data-inset="true" data-theme="d" data-dividertheme="b">
    <li data-role='list-divider'>Ticket id:%(id)s</li><li>Cannot send email! The ticket do not exists!</li></ul>""" % n
    
    import smtplib, socket
    smtphost = 'smtp.terranovanet.it'
    username = 'info@terranovanet.it'
    password = 'terranova$1'
    mailfrom = "CS Carniva2012 <%s>" % (username)
    to = t['email']
    subject = "Your ticket for Carnival party (ID:%(id)s/%(pdfcode)s)" % t
    body = """Dear %s,

please download your ticket (id no. %s/%s) for the CS Carnival from this link:

%s

If you bought more than one ticket you will receive an email for each ticket you bought.
Don't forget to bring with you your ticket.

For any question, do not hesitate to contact us at the email milanocs@gmail.com.

Best regards,

Gianpaolo
""" % (t['name'], t['id'], t['pdfcode'], pdfurl(t))
    
    message = """To: %s
From: %s
Subject: %s
Reply-To: milanocs@gmail.com

%s
""" % (to, mailfrom, subject, body)
    try:
        s = smtplib.SMTP(smtphost)
        try:
            s.login(username, password)
        except smtplib.SMTPException, e:
            return """<ul data-role="listview" data-inset="true" data-theme="d" data-dividertheme="b">
    <li data-role='list-divider'>Email ticket id:%(id)s/%(pdfcode)s</li><li>Authentication failure (SMTP)</li></ul>""" % t
        else:
            s.sendmail(mailfrom, to, message)
    except (socket.gaierror, socket.error, socket.herror, smtplib.SMTPException), e:
        return """<ul data-role="listview" data-inset="true" data-theme="d" data-dividertheme="b">
    <li data-role='list-divider'>Email ticket id:%(id)s/%(pdfcode)s</li><li>ERROR SENDING MAIL !!!</li></ul>""" % t
    else:
        db = load()
        for n in db['tickets']:
            if n['id'] == int(t['id']):
                n['sent'] = datetime.now().strftime("%d-%m-%Y %H:%M")
                break
        save(db)      
        
        return """<ul data-role="listview" data-inset="true" data-theme="d" data-dividertheme="b">
    <li data-role='list-divider'>Email ticket id:%(id)s/%(pdfcode)s</li><li>Mail response sent successfully.</li></ul>""" % t

def checkin(n):
    db = load()
    if db['checkin'] == 'Off':
        print "Content-type: text/html\n\n"
        print "<h1>Check-in mode is currently disabled.</h1>"
        return
    
    for t in db['tickets']:
        if t['pdfcode'] == n:
            if t['checkin'] != False:
                print "Content-type: text/html\n\n"
                print "<h1>Ticket already checked at %(checkin)s</h1>" % t
                return
                
            t['checkin'] = datetime.now().strftime("%d-%m-%Y %H:%M")
            save(db)
            print "Content-type: text/html\n\n"
            print "<h1>Check-in OK!</h1>"
            return
    print "Content-type: text/html\n\n"
    print "<h1>Ticket not found!</h1>"
    
def parse_get_qs(qs, fs, keep_blank_values=0, strict_parsing=0):
    r = {}
    for name_value in qs.split('&'):
        nv = name_value.split('=', 2)
        if len(nv) != 2:
            if strict_parsing:
                raise ValueError, "bad query field: %r" % (name_value,)
            continue
        name = urllib.unquote(nv[0].replace('+', ' '))
        value = urllib.unquote(nv[1].replace('+', ' '))
        if len(value) or keep_blank_values:
            if r.has_key(name):
                r[name].append(value)
            else:
                r[name] = [value]

    # Only append values that aren't already in the FieldStorage's keys;
    # This makes POSTed vars override vars on the query string
    for key, values in r.items():
        if not fs.has_key(key):
            for value in values:
                fs.list.append(cgimodule.MiniFieldStorage(key, value))
    return fs

HEADER = """<!DOCTYPE html>
<html>
<head>
 <meta charset="utf-8">
 <meta name="viewport" content="width=device-width, initial-scale=1">
 <title>Ticket Office</title>
 <link rel="stylesheet" href="http://code.jquery.com/mobile/1.0.1/jquery.mobile-1.0.1.min.css" />
 <link rel="stylesheet" href="../../../lab/ticketoffice/css/jqm-docs.css" />
 <script src="http://code.jquery.com/jquery-1.6.4.min.js"></script>
 <script src="../../../lab/ticketoffice/js/jquery.mobile.themeswitcher.js"></script>
 <script src="../../../lab/ticketoffice/js/jqm-docs.js"></script> 
 <script src="http://code.jquery.com/mobile/1.0.1/jquery.mobile-1.0.1.min.js"></script>
</head>
<body>
<div id="main" data-role="page">
 <div data-role="content">
  <div class="content-secondary">
   <a href="?q=default"><img src="../../../lab/ticketoffice/images/logo.png" alt="Ticket Office" /></a>
   <p>&nbsp;</p>
   <div id="navigation" data-role="collapsible" data-collapsed="true">
   <h3>Show men&ugrave;</h3>
   <ul data-role="listview" data-inset="true" data-theme="c" data-dividertheme="f">
    <li data-role="list-divider">Men&ugrave;</li>
    <li><a href="?q=register">Register ticket</a></li>
    <li><a href="?q=showlist">Show tickets</a></li> 
    <li><a href="?q=settings" data-ajax="false">Settings</a></li>
   </ul>
   </div>
  </div><!--/content-primary--> 
  
  <div class="content-primary">
   <nav>
"""

HEADER_HOME = """<!DOCTYPE html>
<html>
<head>
 <meta charset="utf-8">
 <meta name="viewport" content="width=device-width, initial-scale=1">
 <title>Ticket Office</title>
 <link rel="stylesheet" href="http://code.jquery.com/mobile/1.0.1/jquery.mobile-1.0.1.min.css" />
 <link rel="stylesheet" href="../../../lab/ticketoffice/css/jqm-docs.css" />
 <script src="http://code.jquery.com/jquery-1.6.4.min.js"></script>
 <script src="../../../lab/ticketoffice/js/jquery.mobile.themeswitcher.js"></script>
 <script src="../../../lab/ticketoffice/js/jqm-docs.js"></script> 
 <script src="http://code.jquery.com/mobile/1.0.1/jquery.mobile-1.0.1.min.js"></script>
</head>
<body>
<div id="main" data-role="page">
 <div data-role="content">
  <div class="content-secondary">
   <a href="?q=default"><img src="../../../lab/ticketoffice/images/logo.png" alt="Ticket Office" /></a>
   <div id="jqm-homeheader">
    <h1 id="jqm-logo"></h1>
    <p>A Ticketing Application.</p>
   </div> 
   <p class="intro"><strong>Welcome.</strong> Start managing your tickets.</p>
   <ul data-role="listview" data-inset="true" data-theme="c" data-dividertheme="f">
    <li data-role="list-divider">Men&ugrave;</li>
    <li><a href="?q=register">Register ticket</a></li>
    <li><a href="?q=showlist">Show tickets</a></li> 
    <li><a href="?q=settings" data-ajax="false">Settings</a></li>
   </ul>
  </div><!--/content-primary--> 
  
  <div class="content-primary">
   <nav>
"""

FOOTER = """
    </nav>
    </ul>
   </div>
  </div>
  <div data-role="footer" class="footer-docs" data-theme="c">
   <p>&copy; 2012 Gianpaolo Terranova</p>
  </div> 
</div>
</body>
</html>
</body></html>"""
    
REGISTER_FORM = """<form action='tickets.py' method=post>
<ul data-role="listview" data-inset="true" data-theme="d" data-dividertheme="b">
  <li data-role="list-divider">Register ticket:</li>
<input type='hidden' name='q' value='insert'>
<li data-role="fieldcontain">
<label for=name>Name: </label><input id='name' type='text' name='name'>
</li>
<li data-role="fieldcontain">
<label for=email>Email: </label><input id='email' type='text' name='email'>
</li>
<li data-role="fieldcontain">
<label for='number' class='select'>Number: </label><select id='number' name='number'>
<option value='1'>1</option>
<option value='2'>2</option>
<option value='3'>3</option>
<option value='4'>4</option>
<option value='5'>5</option>
<option value='6'>6</option>
<option value='7'>7</option>
<option value='8'>8</option>
<option value='9'>9</option>
<option value='10'>10</option>
</select>
</li>
<li data-role="fieldcontain">
<label for=payment>Payment method: </label><select id='payment' name='payment'>
<option value='Bank transfer'>Bank transfer</option>
<option value='Paypal'>Paypal</option>
</select>
</li>
<li data-role="fieldcontain">
<label for=trans>Trans id: </label><input id='trans' type='text' name='trans'>
</li>
<li data-role="fieldcontain">
<label for=date>Date (dd/mm/yyyy): </label><input id='date' type='text' name='date'>
</li>
<li class="ui-body ui-body-b"><fieldset class="ui-grid-a"><div class="ui-block-a"><button type="submit" data-theme="d">Cancel</button></div><div class="ui-block-b"><button type="submit" data-theme="a">Submit</button></div></fieldset></li>
</ul>
</form>
"""

SETTINGS_FORM = """<form action='tickets.py' method=get data-ajax="false">
<ul data-role="listview" data-inset="true" data-theme="d" data-dividertheme="b">
  <li data-role="list-divider">Settings</li>
<input type='hidden' name='q' value='save_settings'>
<li data-role="fieldcontain">
<label for=checkin>Check-in: </label><select id='checkin' name='checkin' data-role="slider">
<option value='Off'>Off</option>
<option value='On'>On</option>
</select>
</li>
<li class="ui-body ui-body-b"><fieldset class="ui-grid-a"><div class="ui-block-a"><button type="submit" data-theme="d">Cancel</button></div><div class="ui-block-b"><button type="submit" data-theme="a">Submit</button></div></fieldset></li>
</ul>
</form>
<script>
$(document).bind('pageshow',function(){
   var myselect = $("select:jqmData(role='slider')");
   if (myselect === "undefined") { } else {
   myselect.slider();
   myselect[0].selectedIndex = %d;
   myselect.slider("refresh");
   }
});
</script>
"""

def _openUrl(url, data=None, headers={}):    
    try:
        req = urllib2.Request(url, data, headers)  # create a request object
        handle = urllib2.urlopen(req)                     # and open it
    except IOError, e:
        print 'Failed to open "%s".' % url
        if hasattr(e, 'code'):
            print 'Error code: %s.' % e.code
    else:
        #make sure the response is compressed
        isGZipped = handle.headers.get('content-encoding', '').find('gzip') >= 0
        data = handle.read()            
        if isGZipped:
            d = zlib.decompressobj(16+zlib.MAX_WBITS)
            data = d.decompress(data)
    return data
    
def main():    
    
    params = cgimodule.FieldStorage(keep_blank_values=1)
    params = parse_get_qs(os.environ['QUERY_STRING'], params)
    
        
    args = {}    
    for p in params:
        try:
            args[p] = params[p].value
        except:
            args[p] = [l.value for l in params[p]]

    action = args.pop('q', "default")

    f = open('ticketoffice.log', 'a')
    f.write("%s: %s %s\n" % (datetime.now().strftime("%d-%m-%Y %H:%M"), action, repr(args)))
    f.close()
        
    if action == "showpdf":
        code = args.get('c', None)
        showpdf(code)
    else:
        print "Content-type: text/html\n\n"
    
        if action == "default":
            print HEADER_HOME, "&nbsp;", FOOTER #showlist(unsent=int(unsent)), FOOTER

        elif action == "register":
            print HEADER, REGISTER_FORM, FOOTER

        if action == "showlist":
            unsent = args.get('unsent', 0)
            undownloaded = args.get('undownloaded', 0)
            unchecked = args.get('unchecked', 0)
            print HEADER, showlist(unsent=int(unsent),undownloaded=int(undownloaded),unchecked=int(unchecked)), FOOTER

        elif action == "settings":
            db = load()
            enable_ck = 0
            if db['checkin'] == 'On':
                enable_ck = 1
            print HEADER, SETTINGS_FORM % (enable_ck), FOOTER
                
        elif action == "save_settings":
            db = load()
            db['checkin'] = args.get('checkin', 'Off')
            save(db)
            enable_ck = 0
            if db['checkin'] == 'On':
                enable_ck = 1
            print HEADER, SETTINGS_FORM % (enable_ck), FOOTER

        elif action == "showticket":
            id = args.get('id', None)
            print HEADER, showticket(id), FOOTER
        
        elif action == "email":
            id = args.get('id', None)
            print HEADER, sendmsg(id), FOOTER

        elif action == "delete":
            id = args.get('id', None)
            delete(id)
            print HEADER, showlist(), FOOTER
            
        elif action == "insert":
            t = {}
            for field in ['name','email','payment','trans','date']:
                t[field] = args.get(field, None)
            for n in range(int(args.get('number',1))):
                insert(t)
            print HEADER, showlist(), FOOTER

        elif action == "showlog":
            f = open('ticketoffice.log', 'r')
            data = f.read()
            f.close()
            print "<pre>",data,"</pre>"

        return
    print "Content-type: text/html\n\n"
    print HEADER, showlist(), FOOTER
        
if __name__ == "__main__":
    main()
