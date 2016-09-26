import logging
import datetime
from utils import Dateutils
import stazione
import trainstatus
import threading
import time

FORMAT = '[%(levelname)s] (%(threadName)-9s) %(message)s'
logging.basicConfig(format=FORMAT)

istest = False
exitFlag = 0


# noinspection PyBroadException
class TrainMonitor(threading.Thread):
    def __init__(self, trainno, station, startcheck):
        threading.Thread.__init__(self)
        self.numerotreno = trainno
        self.stazione = station
        self.startchecking = startcheck
        self.setName("#" + trainno)
        self._active = False

        self.status = trainstatus.TRAINSTATUS_NOTRAIN
        self.ritardo = 0
        self.programmata = datetime.datetime.now()
        self.arrivoreale = datetime.datetime.now()
        self.found = False
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def sendmessage(self):
        self.logger.info('[{0}] here is the message:'.format(self.getName()))
        message = 'il treno arriverà a destinazione ' + self.stazione
        if self.programmata is not None:
            message = message + ' alle:' + self.programmata.strftime('%H:%M')
        else:
            message = message + ' alle:' + '<None>'
        if self.ritardo is not None:
            message = message + ' con ritardo di:' + str(self.ritardo)
        else:
            message = message + ' con ritardo di:' + '<None>'
        if self.status is not None:
            message = message + ' con status :' + str(self.status)

        self.logger.info('[{0}] {1}'.format(self.getName(), message))

    @property
    def active(self):
        return self._active

    def shouldmessage(self):
        try:
            self.logger.info(
                '[{0}] here I should check if i have to send message (do nothing now)'.format(self.getName()))
            if self.status == trainstatus.TRAINSTATUS_PARTIALLYCANCELLED:
                return True
            if self.status == trainstatus.TRAINSTATUS_PARTIALLYCANCELLED:
                return True
            if self.status == trainstatus.TRAINSTATUS_BADLASTSAMPLE:
                return True
            if self.status == trainstatus.TRAINSTATUS_LASTSAMPLELATE:
                return True
            if self.status == trainstatus.TRAINSTATUS_RUNNING and self.ritardo > 0:
                return True
        except:
            self.logger.error('[{0}]Exception raised [unknown]'.format((self.getName())), exc_info=True)
            return False

    def run(self):
        self.logger.info('[{1}] train #{0}, started thread:'.format(self.numerotreno, self.getName()))
        train = trainstatus.Trainstatus(self.numerotreno)
        numberofexcept = 0
        sleeptime = datetime.timedelta(minutes=1)

        while sleeptime.total_seconds() > 0:
            try:
                self._active = True
                sleeptime = datetime.timedelta(minutes=1)
                self.logger.info('[{0}] check forecast for station {1}'.format(self.getName(), self.stazione))
                found, status, arrivoreale, programmata, ritardo = train.getforecastex(self.stazione)

                self.status = status
                self.ritardo = ritardo
                self.programmata = programmata
                self.arrivoreale = arrivoreale
                self.found = found

                self.logger.debug('[{0}] {1}'.format(self.getName(),
                                                     trainstatus.Trainstatus.getdescription(status)))
                if status == trainstatus.TRAINSTATUS_NODATA or status == trainstatus.TRAINSTATUS_CALLERROR:
                    self.logger.debug('[{0}] network error'.format(self.getName()))
                    sleeptime = datetime.timedelta(minutes=1)

                if status == trainstatus.TRAINSTATUS_NOTRAIN:
                    sleeptime = datetime.timedelta(minutes=0)

                if status == trainstatus.TRAINSTATUS_PARTIALLYCANCELLED:
                    if self.shouldmessage():
                        self.logger.debug('[{0}] send message - partially cancelled'.format(self.getName()))
                        self.sendmessage()
                    sleeptime = datetime.timedelta(minutes=0)

                if status == trainstatus.TRAINSTATUS_CANCELLED:
                    if self.shouldmessage():
                        self.logger.debug('[{0}] send message - TRAINSTATUS_CANCELLED'.format(self.getName()))
                        self.sendmessage()
                    sleeptime = datetime.timedelta(minutes=0)

                if status == trainstatus.TRAINSTATUS_ARRIVEDSTATION:
                    self.logger.debug('[{0}]  arrivato alla stazione {1}'.format(self.getName(), self.stazione))
                    sleeptime = datetime.timedelta(minutes=0)

                if status == trainstatus.TRAINSTATUS_ARRIVEDLASTSTATION:
                    sleeptime = datetime.timedelta(minutes=0)

                if status == trainstatus.TRAINSTATUS_NOTYETSTARTED:
                    if self.startchecking > datetime.datetime.now():
                        sleeptime = self.startchecking - datetime.datetime.now()

                if status == trainstatus.TRAINSTATUS_RUNNING:
                    self.logger.info(
                        '[{0}] treno in viaggio , ma non ancora arrivato alla stazione di {1}'.format(self.getName(),
                                                                                                      self.stazione))
                    if self.shouldmessage():
                        self.sendmessage()
                    if self.startchecking > datetime.datetime.now():
                        self.logger.info('start checking is bigger then now -> sleep for a while:')
                        sleeptime = self.startchecking - datetime.datetime.now()

                if status == trainstatus.TRAINSTATUS_BADLASTSAMPLE:
                    self.logger.debug('[{0}] treno in viaggio , ultimo rilevamento errato'.format(self.getName()))
                    if self.shouldmessage():
                        self.sendmessage()
                    if  self.startchecking > datetime.datetime.now():
                        self.logger.info('start checking is bigger then now -> sleep for a while:')
                        sleeptime = self.startchecking - datetime.datetime.now()

                if status == trainstatus.TRAINSTATUS_LASTSAMPLELATE:
                    self.logger.error('[{0}] treno in viaggio , ultimo rilevamento vecchio'.format(self.getName()))
                    if self.shouldmessage():
                        self.sendmessage()
                    if  self.startchecking > datetime.datetime.now():
                        self.logger.info('start checking is bigger then now -> sleep for a while:')
                        sleeptime =  self.startchecking - datetime.datetime.now()
            except:
                self.logger.error('[{0}] Exception raised [unknown]'.format(self.getName()), exc_info=True)
                numberofexcept += 1
                if numberofexcept > 5:
                    sleeptime = datetime.timedelta(minutes=0)

            if sleeptime.total_seconds() > 0:
                nextawake = datetime.datetime.now() + sleeptime
                message = '[{0}] sleeping for {1}s from {2} till {3}'.format(self.getName(),
                                                                             sleeptime.strftime('%H:%M:%S'),
                                                                             datetime.datetime.now().strftime('%H:%M'),
                                                                             nextawake.strftime('%H:%M'))
                self.logger.info(message)
                time.sleep(sleeptime.total_seconds())

        self.logger.info('[{0}] stop monitoring'.format(self.getName()))
        self._active = False


def is2monitor(partenza, arrivo, starttime, endtime):
    if istest:
        if partenza is not None and arrivo is not None:
            return True

    if partenza is not None:
        if Dateutils.is_holiday(partenza) and not istest:
            return False
        if starttime < partenza < endtime:
            return True
    if arrivo is not None:
        if Dateutils.is_holiday(arrivo) and not istest:
            return False
        if starttime < arrivo < endtime:
            return True
    return False



def mainlogic(startstation,endstation,istest):
    currenttime = datetime.datetime.now().time()
    logging.info('[main] current time is ' + currenttime.strftime("%H:%M"))
    starttime_itineraraio = datetime.time(0, 30).strftime("%H:%M")
    logging.info('[main] we ask for journey between {0} and {1} starting from {2}'.format(startstation, endstation,
                                                                                          starttime_itineraraio))

    if istest:
        starttime_monitor = Dateutils.time_addasdatetime(currenttime.hour, currenttime.minute, -30)
        endtime_monitor = Dateutils.time_addasdatetime(currenttime.hour, currenttime.minute, + 120)
    else:
        starttime_monitor = Dateutils.time_addasdatetime(8, 4, -60)
        endtime_monitor = Dateutils.time_addasdatetime(8, 4, +10)

    logging.info('[main] stazione di partenza: {0}'.format(startstation))
    albenga = stazione.Stazione(startstation)
    logging.info('[main] retriving details  of {0}'.format(startstation))
    albenga.getdettagi()
    logging.info('[main] we check journeys between {0} and {1}'.format(starttime_monitor.strftime("%H:%M"),
                                                                       endtime_monitor.strftime("%H:%M")))

    dataItinerario = albenga.itinerario(endstation, starttime_itineraraio)
    monitors = {}
    for soluzione in dataItinerario[0]['soluzioni']:
        try:
            numerotreno = soluzione['vehicles'][0]['numeroTreno']
            partenzateorica = datetime.datetime.strptime(soluzione['vehicles'][0]['orarioPartenza'],
                                                         '%Y-%m-%dT%H:%M:%S')
            arrivoteorico = datetime.datetime.strptime(soluzione['vehicles'][0]['orarioArrivo'], '%Y-%m-%dT%H:%M:%S')
            if is2monitor(partenzateorica, arrivoteorico, starttime_monitor, endtime_monitor):
                logging.info('[main] train #{0} of {1} will be monitored'.format(
                    soluzione['vehicles'][0]['numeroTreno'],
                    soluzione['vehicles'][0]['orarioArrivo']))

                startchecking = arrivoteorico + datetime.timedelta(minutes=-30)
                monitors[numerotreno] = TrainMonitor(numerotreno, startstation, startchecking)
                monitors[numerotreno].setName('#' + numerotreno)
                logging.info('[main] train #{0}, starting thread:'.format(numerotreno))
                monitors[numerotreno].start()
            else:
                logging.info('[main] train #{0} of {1} will be skipped'.format(
                    soluzione['vehicles'][0]['numeroTreno'],
                    soluzione['vehicles'][0]['orarioArrivo']))
        except:
            logging.error('[main] Exception raised [unknown]', exc_info=True)



    active = 1
    stopped = 0

    while active > 0 and stopped < len(monitors):
        active = 0
        stopped = 0
        for monitor in monitors.values():
            if monitor.active:
                logging.info('train [{0}]'.format(monitor.getName()))
                active += 1
            else:
                stopped += 1
        logging.info('threads: active #{0} stopped #{1} totals #{2}'.format(active, stopped, len(monitors)))
        time.sleep(60)

    logging.info('[main] reached end of monitor ' + endtime_monitor.strftime("%H:%M"))
    logging.info('bye bye!')


if __name__ == '__main__':
    istest = True
    startstation = 'Albenga'
    endstation = 'Savona'
    mainlogic(startstation,endstation,istest)




