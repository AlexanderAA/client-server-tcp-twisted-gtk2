import gtk
#import gobject

from twisted.internet import gtk2reactor # we use gtk-2.0
# to install the proper reactor this must be called before importing reactor from twisted.internet
gtk2reactor.install()

from twisted.internet import reactor, task
from twisted.spread import pb

import time
import os
import pickle
import platform

APP_NAME = "Picture of the day"
APP_AUTHORS = ("Aliaksandr Abushkevich",)
APP_DESCRIPTION = "Sample Project"
APP_VERSION = "0.1"
APP_ICON_NAME = "vt"

IMAGE_WINDOW_TIMEOUT_SEC = 1.5

SERVER_IP = "127.0.0.1"
SERVER_PORT = 8482

TMP_PIC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temporary", "tmp_img.jpg")


class AppGUI:
    '''
    Implemets GUI logic
    '''
    def __init__(self):
        #Initialize GUI
        self._create_gui()
        reactor.run()

    def _create_gui(self):
        '''
        Makes initial setup of GUI and connects some functions to events 
        '''
        # Tries to find application icon
        # In windows icon will not be found, so later we will try to get icon directly from file
        theme = gtk.icon_theme_get_default()
        if not theme.has_icon(APP_ICON_NAME):
            theme.prepend_search_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons"))
        if theme.has_icon(APP_ICON_NAME):
            self._icon_name = APP_ICON_NAME
        else:
            self._icon_name = gtk.STOCK_APPLY

        # Builds tray icon
        self.tray = gtk.StatusIcon()
        
        # In windows gtk.icon_theme theme cannot find icon, so we will load icon manually
        # Lets check if our operating system is windows:
        if platform.system() == 'Windows': # Windows OS
            # Getting the path to icon:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons/hicolor/48x48/apps/%s.png" % APP_ICON_NAME)
            if os.path.exists(icon_path): # Icon is found
                self.tray.set_from_file(icon_path) #Gets icon from file
            else: # File with icon not found
                self.tray.set_from_icon_name(self._icon_name)
        else: # NOT Windows OS (Linux, ...)
            self.tray.set_from_icon_name(self._icon_name)
        
        self.tray.connect('popup-menu', self._on_popup_menu)
        self.tray.connect('activate', self._on_activate)

        self.tray.set_visible(True)

        # Creates menu (on right mouse click)
        self._create_right_menu()
        
        # Tooltip
        if platform.system() == 'Windows':
            self.tray.set_tooltip("Picture of the day - was not tested in Windows, run me in Linux please!")
        else:
            self.tray.set_tooltip("Picture of the day - click on me!")
        
        # Initialize popup window
        self._image_window = gtk.Window(gtk.WINDOW_POPUP)
        self._image_window.set_default_size(300,200)
        self._image_window.set_gravity(gtk.gdk.GRAVITY_NORTH)
        
        # Reads image from filesystem        
        self._image = gtk.Image()

        # Uses gtk.Fixed widget to show the image
        fixed = gtk.Fixed()
        fixed.put(self._image, 0, 0)
        self._image_window.add(fixed)
        self._image_window.get_children
        
        # Loads first image to display immediately, when user clicks on tray icon
        reactor.callLater(0.05, self._fetch_image)
        
        
    def _create_right_menu(self):
        '''
        Creates menu (on right mouse click)
        '''
        self._rmenu = gtk.Menu()
        about = gtk.ImageMenuItem(stock_id=gtk.STOCK_ABOUT)
        about.connect("activate", self._on_about_clicked)
        quit = gtk.ImageMenuItem(stock_id=gtk.STOCK_QUIT)
        quit.connect("activate", self.exit)
        self._rmenu.add(about)
        self._rmenu.add(quit)
        self._rmenu.show_all()
            
    def _on_popup_menu(self, status, button, time):
        '''
        Shows menu (on right mouse click)
        '''
        self._rmenu.popup(None, None, gtk.status_icon_position_menu, button, time, self.tray)
 
    def _on_activate(self, *args):
        '''
        Shows popup window with image, fetches next image from server
        '''
        # SHOWS image from local cache
        df_show = task.deferLater(reactor, 0, self._show_image)
        # Shows warning in case of error
        df_show.addErrback(self._show_warning)
        
        # FETCHES NEXT image, save in cache
        df_fetch = task.deferLater(reactor, 0.1, self._fetch_image)
        # Shows warning in case of error
        df_fetch.addErrback(self._show_warning)
        
        
    def _show_image(self):
        '''
        Reads image from local cache (file), shows popup window with image.
        '''
        # Hide previously opened popup windows
        self._image_window.hide_all()
        # We need to cancel "close window" task for previously opened popup window
        # If the window_close task is not cancelled and someone clicks on icon a lot, last window opened could be 
        # closed much earlier than expected.

        # If we use gobject:
        #if hasattr(self, '_source_id'):
        #    gobject.source_remove(self._source_id)
        # If we use twisted:    
        if hasattr(self, '_wnd_hide') and hasattr(self._wnd_hide, 'active'):
            if self._wnd_hide.active(): #is the task of closing the window still pending?
                self._wnd_hide.cancel() #if yes, cancel it

        
        # Adjusts window position
        # We can not get coordinates of the icon -> we have to get mouse pointer coords (when user clicks on icon)
        # it is ugly. This could help:
        #screen, area, orientation = self.tray.get_geometry()
        rootwin = self._image_window.get_screen().get_root_window()
        mouse_x, mouse_y, mods = rootwin.get_pointer()
        
        # Try to adjust the position of the window
        # TODO: fix this to allow any position of the app icon (on the right panel, left panel, ...)
        if mouse_y<150: #top
            self._image_window.move(mouse_x-150, mouse_y+20)
        if mouse_y>=150: #bottom
            self._image_window.move(mouse_x-150, mouse_y-20-200)
        
        if os.path.exists(TMP_PIC_PATH):
            self._image.set_from_file(TMP_PIC_PATH)
            # Shows window with gtk.Fixed widget and image
            self._image_window.show_all()
        else:
            self._show_warning("Operation failed: Cached image do not exist")

        # Closes window after IMAGE_WINDOW_TIMEOUT_SEC seconds. 
        # This could be made using gobject:
        #self._source_id = gobject.timeout_add(IMAGE_WINDOW_TIMEOUT_SEC*1000, self._on_window_close)
        # Or with Twisted:
        self._wnd_hide = reactor.callLater(IMAGE_WINDOW_TIMEOUT_SEC, self._image_window.hide_all)

    def _show_warning(self, args):
        '''
        Must show warnings on every errBack. Or log them.
        '''
        pass
        
    def _on_about_clicked(self, widget):
        '''
        Shows About dialog with information about author and version
        '''
        dlg = gtk.AboutDialog()
        dlg.set_name(APP_NAME)
        dlg.set_comments(APP_DESCRIPTION)
        dlg.set_version(APP_VERSION)
        dlg.set_authors(APP_AUTHORS)
        dlg.set_logo_icon_name(self._icon_name)
        dlg.run()
        dlg.destroy()

    def  exit(self, *args):
        '''
        Closes the application
        '''
        reactor.stop()
        gtk.main_quit()

    def _fetch_image(self):
        '''
        Fetches an image from server
        '''
        factory = pb.PBClientFactory()
        reactor.connectTCP(SERVER_IP, SERVER_PORT, factory)
        d = factory.getRootObject()
        # Calls remote function "serve_random_image" to request an image from server
        d.addCallback(lambda object: object.callRemote("serve_random_image", "give me an image, please"))
        d.addCallback(self._write_image)
        d.addErrback(self._show_warning)
      
    def _write_image(self, img_data):
        '''
        Writes received data to local cache (Currently, to a file.)
        img_data = pickle.dumps({'file_name': 'filename', 'file_data': 'contents of file'})
        '''
        img_dict = pickle.loads(img_data)
        print img_dict['file_name']
        try:
            image_file = open(TMP_PIC_PATH, 'w')
            image_file.write(img_dict['file_data'])
            image_file.close()
        except:
            self._show_warning('Operation failed: Write to cache')

if __name__ == "__main__":
    '''
    If executed directly, print an error message.
    '''
    print 'This module is not intended to be executed directly. Execute client.py, please.'
