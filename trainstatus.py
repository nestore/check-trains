import logging
from utils import Dateutils
import datetime
from viaggiatrenonew import Viaggiatrenonew

FORMAT = '[%(levelname)s] (%(threadName)-9s) %(message)s'
logging.basicConfig(format=FORMAT)

TRAINSTATUS_NODATA = -999
TRAINSTATUS_CALLERROR = -666
TRAINSTATUS_DATAOK = 0

TRAINSTATUS_ARRIVEDLASTSTATION = 4
TRAINSTATUS_ARRIVEDSTATION = 3
TRAINSTATUS_LASTSAMPLELATE = 2
TRAINSTATUS_DATANOTEXPIRED = 1
TRAINSTATUS_RUNNING = 0
TRAINSTATUS_NOTRAIN = -1
TRAINSTATUS_CANCELLED = -2
TRAINSTATUS_NOTYETSTARTED = -3
TRAINSTATUS_NOTSTARTED = -3
TRAINSTATUS_PARTIALLYCANCELLED = -4
TRAINSTATUS_BADLASTSAMPLE = -5


class Trainstatus:
    def __init__(self, trainnumber, expiringtime=120, sampleexpiringtime=60 * 4):
        self.viaggiatreno = Viaggiatrenonew()
        self.trainnumber = trainnumber
        self.departureID = None
        self.train_status = None
        self.lastcheck = None
        self.expiringtime = expiringtime  # in seconds
        self.sampleexpiringtime = sampleexpiringtime  # in seconds
        self.ritardo = 0
        self.ultimorilevamento = datetime.datetime.now() - datetime.timedelta(hours=-24)
        self.currentstatus = TRAINSTATUS_NOTRAIN
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # self.processstatus()



    @staticmethod
    def getdescription(status):
        if status == TRAINSTATUS_NODATA:
            return "object contains no data"
        if status == TRAINSTATUS_CALLERROR:
            return "call error"

        if status == TRAINSTATUS_ARRIVEDLASTSTATION:
            return "TRAIN ARRIVED TO LAST STATION"
        if status == TRAINSTATUS_ARRIVEDLASTSTATION:
            return "TRAIN ARRIVED TO FORECAST STATION"
        if status == TRAINSTATUS_ARRIVEDLASTSTATION:
            return "LAST SAMPLE was LATE"
        if status == TRAINSTATUS_DATANOTEXPIRED:
            return "DATA NOT EXPIRED"
        if status == TRAINSTATUS_RUNNING:
            return "TRAIN RUNNING (before FORECAST STATION)"
        if status == TRAINSTATUS_NOTRAIN:
            return "TRAIN NUMBER NOT PRESENT"
        if status == TRAINSTATUS_CANCELLED:
            return "TRAIN CANCELLED"
        if status == TRAINSTATUS_NOTYETSTARTED:
            return "TRAIN NOT YET STARTED"
        if status == TRAINSTATUS_PARTIALLYCANCELLED:
            return "TRAIN PARTIALLY CANCELLED"
        if status == TRAINSTATUS_BADLASTSAMPLE:
            return "BAD LAST SAMPLE"
        return "UNKNOWN STATUS"



    def getdepartures(self, departurenumber=1):
        departures = self.viaggiatreno.call('cercaNumeroTrenoTrenoAutocomplete', self.trainnumber)
        retvalue = len(departures)
        if len(departures) == 0:
            self.logger.warning("Train {0} does not exists.".format(self.trainnumber))
            return False
        if len(departures) == 1:
            self.departureID = departures[0][departurenumber]
        else:
            # TODO: handle not unique train numbers, when len(departures) > 1
            self.departureID = departures[0][departurenumber]
        return retvalue

    def __isexpired(self, force=False):
        if force:
            return True
        if self.train_status is None:
            return True
        elapsedrequest = (datetime.datetime.now() - self.lastcheck).total_seconds()
        if elapsedrequest > self.expiringtime:
            return True
        return False

    @property
    def trainstatus(self):
        if self.__isexpired(False):
            self.processstatus(False)
        return self.currentstatus

    def __getstatus(self, force=False):

        if not self.__isexpired(force):
            return TRAINSTATUS_DATANOTEXPIRED

        self.train_status = None
        if self.departureID is None:
            if self.getdepartures() == 0:
                return TRAINSTATUS_NOTRAIN
        try:
            self.train_status = self.viaggiatreno.call('andamentoTreno', self.departureID, self.trainnumber)
            self.lastcheck = datetime.datetime.now()
        except:
            self.logger.error('Exception raised [unknown]', exc_info=True)
            return TRAINSTATUS_CALLERROR

        if self.train_status is None:
            self.logger.error('no data from call <andamentoTreno>')
            return TRAINSTATUS_NODATA

        return TRAINSTATUS_DATAOK

    def isbadstatus(self):
        retvalue = self.__getstatus(False)
        breturn = retvalue == TRAINSTATUS_NOTRAIN or retvalue == TRAINSTATUS_CALLERROR or retvalue == TRAINSTATUS_NODATA
        return breturn

    @property
    def lastsampleelapsed(self):
        return (datetime.datetime.now() - self.ultimorilevamento).total_seconds()

    def processstatus(self, force=False):

        retvalue = self.__getstatus(force)

        if retvalue == TRAINSTATUS_NOTRAIN:
            self.currentstatus = retvalue
            return False
        if retvalue == TRAINSTATUS_CALLERROR:
            self.currentstatus = retvalue
            return False
        if retvalue == TRAINSTATUS_NODATA:
            self.currentstatus = retvalue
            return False

        if self.train_status['tipoTreno'] == 'ST' or self.train_status['provvedimento'] == 1:
            self.logger.warning("Train {0} cancelled".format(self.trainnumber))
            self.currentstatus = TRAINSTATUS_CANCELLED
            return True

        if self.train_status['oraUltimoRilevamento'] is None:
            self.logger.info("Train {0} has not yet departed".format(self.trainnumber))
            self.logger.info("Scheduled departure {0} from {1}".format(
                Dateutils.format_timestamp(self.train_status['orarioPartenza']),
                self.train_status['origine']))
            self.currentstatus = TRAINSTATUS_NOTYETSTARTED
            return False

        if self.train_status['tipoTreno'] in ('PP', 'SI', 'SF'):
            self.logger.warning("Train partially cancelled: {0}".format(self.train_status['subTitle']))
            self.currentstatus = TRAINSTATUS_PARTIALLYCANCELLED
            return self.currentstatus >= 0

        if not Dateutils.check_timestamp(self.train_status['oraUltimoRilevamento']):
            self.currentstatus = TRAINSTATUS_BADLASTSAMPLE
            return False

        self.ultimorilevamento = Dateutils.convert_timestamp(self.train_status['oraUltimoRilevamento'])

        if self.lastsampleelapsed > self.sampleexpiringtime:
            self.currentstatus = TRAINSTATUS_LASTSAMPLELATE
            self.ritardo = max(self.lastsampleelapsed / 60, self.ritardo)
            return True

        self.ritardo = self.train_status['ritardo']
        self.currentstatus = TRAINSTATUS_RUNNING
        return True

    def getforecastex(self, forecaststation, force=False):
        retvalue = self.processstatus(force)

        # GOOD DATA,STATUS,ISFORECAST,
        if not retvalue:
            # ok we are in a very bad status
            # NOTRAIN, CALLERROR, NODATA, BADLASTSAMPLE
            return False, self.currentstatus, None, None, self.ritardo

        arrivoreale = None
        programmata = None
        found = False
        for fermata in self.train_status['fermate']:
            if fermata['tipoFermata'] == 'P':
                if Dateutils.is_valid_timestamp(fermata['partenzaReale']):
                    self.currentstatus = TRAINSTATUS_RUNNING
                else:
                    self.currentstatus = TRAINSTATUS_NOTYETSTARTED

            if fermata['stazione'].upper() == forecaststation.upper():
                found = True
                arrivoreale = Dateutils.convert_timestamp(fermata['arrivoReale'])
                programmata = Dateutils.convert_timestamp(fermata['programmata'])
                if Dateutils.is_valid_timestamp(fermata['arrivoReale']):
                    self.currentstatus = TRAINSTATUS_ARRIVEDSTATION

            if fermata['tipoFermata'] == 'A':
                if Dateutils.is_valid_timestamp(fermata['arrivoReale']):
                    self.currentstatus = TRAINSTATUS_ARRIVEDLASTSTATION

        return found, self.currentstatus, arrivoreale, programmata, self.ritardo


# def getforecast(self, forecaststation, force = False):
#
#       self.processstatus(force)
#        self.train_status['stazioneUltimoRilevamento']
#
#        for fermata in self.train_status['fermate']:
#            try:
#                stationname = fermata['stazione']
#                msg = fermata['stazione'] + ' [' + fermata['tipoFermata'] + '] ritardo:' + str(self.ritardo) + ','
#                scheduled = Dateutils.convert_timestamp(fermata['programmata'])
#                partenzaTeorica = Dateutils.convert_timestamp(fermata['partenza_teorica'])
#                sscheduled = Dateutils.format_timestamp(fermata['programmata'])
#                spartenzaTeorica = Dateutils.format_timestamp(fermata['partenza_teorica'])
#                msg = msg + 'programmata:' + sscheduled + ', teorica:' + spartenzaTeorica
#                if fermata['tipoFermata'] == 'P':
#                    delay = fermata['ritardoPartenza']
#                    spartenzaReale = Dateutils.format_timestamp(fermata['partenzaReale'])
#                    partenzaReale = Dateutils.convert_timestamp(fermata['partenzaReale'])
#                    msg = msg + ', partenzaReale:' + spartenzaReale
#                    msg = msg + ', ritardo (Partenza):' + str(delay)
#                    if fermata['arrivoReale'] is None:
#                        inviaggio = False
#                if fermata['tipoFermata'] == 'F':
#                    if fermata['arrivoReale'] is not None:
#                        sarrivoReale = Dateutils.format_timestamp(fermata['arrivoReale'])
#                    else:
#                        sarrivoReale = ''
#                    delay = fermata['ritardoArrivo']
#                    msg = msg + ', arrivo Reale:' + sarrivoReale
#                    msg = msg + ', ritardo (Arrivo):' + str(delay)
#                if fermata['tipoFermata'] == 'A':
#                    if fermata['arrivoReale'] is not None:
#                        sarrivoReale = Dateutils.format_timestamp(fermata['arrivoReale'])
#                    else:
#                        sarrivoReale = ''
#                    delay = fermata['ritardoArrivo']
#                    msg = msg + ', arrivo Reale:' + sarrivoReale
#                    msg = msg + ', ritardo (Arrivo):' + str(delay)
#
#                if fermata['stazione'] == forecaststation:
#                    self.logger.info('***' + msg)
#                    forecastfermata = fermata
#                else:
#                    self.logger.info(msg)
#            except:
#                self.logger.error('Exception raised [unknown]', exc_info=True)
#        return forecastfermata,self.ritardo




if __name__ == '__main__':
    train = Trainstatus(11356)
    train.getdepartures()
    train.processstatus()
    train.getforecastex('Albenga')
    logging.info('done')
