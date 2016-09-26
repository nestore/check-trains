import logging
import datetime
import utils

from viaggiatrenonew import Viaggiatrenonew

ITINERARION_CALLERROR = -1
STAZIONE_CALLERROR = -1
STAZIONE_CALLOK = 0

FORMAT = '[%(levelname)s] (%(threadName)-9s) %(message)s'
logging.basicConfig(format=FORMAT)

region_codes = {
    1: "Lombardia",
    2: "Liguria",
    3: "Piemonte",
    4: "Valle d'Aosta",
    5: "Lazio",
    6: "Umbria",
    7: "Molise",
    8: "Emilia Romagna",
    10: "Friuli-Venezia Giulia",
    11: "Marche",
    12: "Veneto",
    13: "Toscana",
    14: "Sicilia",
    15: "Basilicata",
    16: "Puglia",
    17: "Calabria",
    18: "Campania",
    19: "Abruzzo",
    20: "Sardegna",
    22: "Trentino Alto Adige"
}


class Stazione:
    #prova
    def __init__(self, nomestazione):
        self.viaggiatreno = Viaggiatrenonew(verbose=False)
        self._stazione = nomestazione
        self._stazioneid = None
        self._regioneID = None
        self._city = None
        self._lat = 0
        self._lon = 0
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)


    def getdettagi(self):

        try:
            if self._stazioneid is None:
                self.getdata()

            details = self.viaggiatreno.call('dettaglioStazione', self._stazioneid, self._regioneID)
        except Exception:
            self.logger.error('Exception raised [unknown]', exc_info=True)
            return STAZIONE_CALLERROR
        self._city = details['nomeCitta']
        self._lat = details['lat']
        self._lon = details['lon']

    def getdata(self):

        try:
            datastazione = self.viaggiatreno.call('cercaStazione', self._stazione)
        except Exception:
            self.logger.error('Exception raised [unknown]', exc_info=True)
            return STAZIONE_CALLERROR
        self._stazioneid = (str(datastazione[0]['id']))
        try:
            self._regioneID = self.viaggiatreno.call('regione', self._stazioneid)
        except Exception:
            self.logger.error('Exception raised [unknown]', exc_info=True)
            return STAZIONE_CALLERROR
        return STAZIONE_CALLOK

    def arrivi(self):

        datatempo = datetime.datetime.now().strftime('%a %b %d %Y %H:%M:%S GMT+0100')

        if self._stazioneid is None:
            self.getdata()
        try:
            dataarrivi = self.viaggiatreno.call('arrivi', self._stazioneid, datatempo)
            return STAZIONE_CALLOK, dataarrivi
        except Exception:
            self.logger.error('Exception raised [unknown]', exc_info=True)
            return STAZIONE_CALLERROR, None

    def partenze(self):

        datatempo = datetime.datetime.now().strftime('%a %b %d %Y %H:%M:%S GMT+0100')

        if self._stazioneid is None:
            self.getdata()
        try:
            datapartenza = self.viaggiatreno.call('partenze', self._stazioneid, datatempo)
            return STAZIONE_CALLOK, datapartenza
        except Exception:
            self.logger.error('Exception raised [unknown]', exc_info=True)
            return STAZIONE_CALLERROR, None

    def itinerario(self, stazionearrivo, orario=None):

        try:
            dataitinerario = self.viaggiatreno.call('cercaStazione', stazionearrivo)
        except:
            self.logger.error('Exception raised [unknown]', exc_info=True)
            return ITINERARION_CALLERROR

        arrivoid = (str(dataitinerario[0]['id']))
        arrivoid = arrivoid.replace('S00', '')
        arrivoid = arrivoid.replace('S0', '')
        arrivoid = arrivoid.replace('S', '')

        partenzaid = self._stazioneid.replace('S00', '')
        partenzaid = partenzaid.replace('S0', '')
        partenzaid = partenzaid.replace('S', '')

        if orario is None:
            tempo = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        else:
            otempo = utils.Dateutils.getdatimefromtimestring(orario)
            if otempo is None:
                return ITINERARION_CALLERROR
            tempo = otempo.strftime('%Y-%m-%dT%H:%M:%S')
        try:
            dataitinerario = self.viaggiatreno.call('soluzioniViaggioNew', partenzaid, arrivoid, tempo)
        except:
            self.logger.error('Exception raised [unknown]', exc_info=True)
            return ITINERARION_CALLERROR

        return dataitinerario, True, None


if __name__ == '__main__':
    station = Stazione('Albenga')
    station.getdettagi()
    retvalue, data = station.arrivi()
    retvalue, data = station.partenze()
    retvalue, data = station.itinerario("SAVONA")
    logging.info('done!')
