from zope.interface import implements
from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application.internet import TCPServer
from twisted.spread import pb

from vt_server.vt_server import ImageServer

class Options(usage.Options):
    optParameters = [["port", "p", 8482, "Port number to listen on."]]

class ImageServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "vt_server"
    description = "Server for Sample project"
    options = Options

    def makeService(self, options):
        serverfactory = pb.PBServerFactory(ImageServer())
        return TCPServer(int(options["port"]), serverfactory)

serviceMaker = ImageServiceMaker()
