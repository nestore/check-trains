import urllib.request
import json
import re
from utils import IPgetter
import logging
import urllib.parse
FORMAT = '[%(levelname)s] (%(threadName)-9s) %(message)s'
logging.basicConfig(format=FORMAT)

class Messages:

    def __init__(self,apikey, googleto, devices):
        self.mode = "Automate"
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self._secret = apikey
        self._recipient = googleto
        self._device = devices
        self.httprequest = 'https://llamalab.com/automate/cloud/message'
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)


    def ____send_message(self, message="", **kwargs):
        self.logger.debug("Sending to: %s, %s", self._recipient, str(self._device))
        params = {
            "secret": self._secret,
            "to": self._recipient,
            "device": self._device,
            "payload": message
        }

        req = urllib.request.Request(self.httprequest,
                                     data=params,
                                     headers={'content-type': 'application/json'})


    #POST  HTTP/1.1
    #
    #Content-Type: application/x-www-form-urlencoded
    def ___makeurlencodedpost(self,to,payload = None,device = None):
        try:
            httpquery = None
            if to is not None:
                httpquery = httpquery + '&to=' + urllib.parse.quote(str(to), safe='')
            if payload is not None:
                httpquery = httpquery + '&payload=' + urllib.parse.quote(str(payload), safe='')
            if device is not None:
                httpquery = httpquery + '&payload=' + urllib.parse.quote(str(device), safe='')
            httpquery = self.httprequest + '?' + httpquery
            self.logger.debug(httpquery)
            req = urllib.request.urlopen(httpquery)
            data = req.read().decode('utf-8')
            self.logger.info(data)
        except:
            self.logger.error('[main] Exception raised [unknown]', exc_info=True)
    #POST /automate/cloud/message HTTP/1.1
    #Host: llamalab.com
    #Content-Type: application/json
    #
    #{
    #  "secret": null,
    #  "to": null,
    #  "device": null,
    #  "payload": "Hello World!"
    #}

    def makejsonpost(self,message):
        try:

            payload = {
                "requestip":IPgetter().get_externalip(),
                "message" :message
            }

            params = {
                "secret": self._secret,
                "to": self._recipient,
                "device": self._device,
                "payload": payload
            }

            req = urllib.request.Request(self.httprequest)
            req.method = 'POST'
            req.data = json.dumps(params).encode('utf8')
            req.add_header('content-type','application/json')
            #req.add_header('Content-Length',99999)
            response = urllib.request.urlopen(req)
            if response.status != 200 or response.msg != 'OK':
                answerback = response.read().decode('utf8')
                return 0
            else:
                answerback = response.read().decode('utf8')
                self.logger.debug(answerback)
                return response.status
        except:
            self.logger.error('[main] Exception raised [unknown]', exc_info=True)
            return  -1



if __name__ == '__main__':
    test = Messages('1.8mkNccRiWydOq92jcaV7bo-KyswL1re0NrIPid-fPLk=','emanuele.marenco@gmail.com',None)
    test.makejsonpost('Hallo wolrd!')
