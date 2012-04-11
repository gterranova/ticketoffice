#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
del sys.setdefaultencoding

from time import gmtime, strftime
import os, json

import wx
import thread

import pyserver

# Check we're not using an old version of Python. We need 2.4 above because some modules (like subprocess)
# were only introduced in 2.4.
if int(sys.version_info[1]) <= 3:
    print 'You are using an outdated version of Python. Please update to v2.4 or above (v3 is not supported).'
    sys.exit(2)
  
class RedirectText:
    def __init__(self,aWxTextCtrl):
        self.out=aWxTextCtrl

    def write(self,string):
        self.out.WriteText(string)

class StoppableHTTPServer(pyserver.HTTPServer):

    def server_bind(self):
        pyserver.HTTPServer.server_bind(self)
        self.socket.settimeout(1)
        self.run = True

    def get_request(self):
        while self.run:
            try:
                sock, addr = self.socket.accept()
                sock.settimeout(None)
                return (sock, addr)
            except socket.timeout:
                pass

    def stop(self):
        print "Stopping..."
        self.run = False

    def serve(self):
        while self.run:
            self.handle_request()
        print "Stopped!"

class MyFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, pos=(100, 100))
       
        self.tbicon = wx.TaskBarIcon()
        self.tbicon.SetIcon(self.GetIcon(wx.ART_CROSS_MARK), "Python Web Server")

        # Bind some events to it
        wx.EVT_TASKBAR_LEFT_DCLICK(self.tbicon, self.OnToggle) # left click
        wx.EVT_TASKBAR_RIGHT_UP(self.tbicon, self.ShowMenu) # single left click
        wx.EVT_CLOSE(self,self.OnClose) # triggered when the app is closed, which deletes the icon from tray

        # build the menu that we'll show when someone right-clicks
        self.menu = wx.Menu() # the menu object

        self.menu.Append(101, 'Start') # Start
        wx.EVT_MENU(self, 101, self.OnMenuStart) # Bind a function to it
        
        self.menu.Append(102, 'Stop') # Stop
        wx.EVT_MENU(self, 102, self.OnMenuStop) # Bind a function to it

        if 1:
            self.menu.Append(103, 'Show log...') # Show log
            wx.EVT_MENU(self, 103, self.OnMenuShowLog) # Bind a function to it

        self.menu.Append(104, 'Close') # Close
        wx.EVT_MENU(self, 104, self.OnMenuClose) # Bind a function to it

        if 1:
            self.log = wx.TextCtrl(self, -1, size=(500,400), style = wx.TE_MULTILINE|wx.TE_READONLY| wx.HSCROLL)
            sys.stdout=RedirectText(self.log)
            sys.stderr=RedirectText(self.log)
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(self.log, 1, wx.EXPAND)
            self.SetSizer(sizer)
            self.Layout()

        else:
            self.log = self.dummylog
        self.httpd = None

    def GetIcon(self, id, client=wx.ART_OTHER, size=wx.DefaultSize):
        return wx.ArtProvider.GetIcon(id, client, size)
    
    def OnClose(self, evt):
        self.Show(False)
        pass
        
    def ShowMenu(self, event):
        self.PopupMenu(self.menu) # show the popup menu

    def dummylog(self, text, c=None):
        return
        
    def OnMenuStart(self, event):
        #Start the worker thread
        #self.worker = WorkerThread()

        #e.g...
        server_address = ('', 8000)
        self.httpd = StoppableHTTPServer(server_address, pyserver.HTTPRequestHandler)
        sa = self.httpd.socket.getsockname()
        print "Serving HTTP on %s port %d..." % (sa[0], sa[1])
        thread.start_new_thread(self.httpd.serve, ())
        self.tbicon.SetIcon(self.GetIcon(wx.ART_TICK_MARK), "Python Web Server")        

    def OnMenuStop(self, event):
        #Stop the worker thread
        #self.worker.stop()
        if self.httpd:
            self.httpd.stop()
            self.httpd = None
            self.tbicon.SetIcon(self.GetIcon(wx.ART_CROSS_MARK), "Python Web Server")            

    def OnToggle(self, event):
        if self.httpd:
            self.OnMenuStop(event)
        else:
            self.OnMenuStart(event)

    def OnMenuShowLog(self, event):
        if 1:
            if not self.IsShown():
                self.Show()
            else:
                self.Show(False)
       
    def OnMenuClose(self, evt):
        self.tbicon.RemoveIcon() # remove the systemtray icon when the program closes
        wx.GetApp().ExitMainLoop()        

        
class MyApp(wx.App): 
    def OnInit(self):
        self.frame = MyFrame(None, -1, "Python Webserver")     
        self.frame.Show(False)
        self.SetTopWindow(self.frame)
        return True

def main():
    app = MyApp(redirect=False)
    app.MainLoop()


if __name__ == "__main__":
    main()

    
