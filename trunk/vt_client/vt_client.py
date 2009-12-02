import gtk

from ui import AppGUI

if __name__ == "__main__":
    gtk.gdk.threads_init()
    app = AppGUI()
    try:
        gtk.main()
        
    except KeyboardInterrupt:
        app.exit()
