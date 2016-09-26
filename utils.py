import os
import json
# from datetime import date, time, timedelta
import datetime
import logging
import re
import random
import urllib.request

FORMAT = '[%(levelname)s] (%(threadName)-9s) %(message)s'
logging.basicConfig(format=FORMAT)


class Dateutils:
    __italian_holidays = (
        '01-01', '06-01', '25-04', '01-05', '02-06',
        '15-08', '01-11', '08-12', '25-12', '26-12'
    )

    @staticmethod
    def easter(year):
        a = year % 19
        b = year // 100
        c = year % 100
        d = (19 * a + b - b // 4 - ((b - (b + 8) // 25 + 1) // 3) + 15) % 30
        e = (32 + 2 * (b % 4) + 2 * (c // 4) - d - (c % 4)) % 7
        f = d + e - 7 * ((a + 11 * d + 22 * e) // 451) + 114
        month = f // 31
        day = f % 31 + 1
        return datetime.date(year, month, day)

    @staticmethod
    def is_holiday(holidaydate):
        if holidaydate.isoweekday() > 5:
            return True
        ddmm = holidaydate.strftime('%d-%m')
        east = Dateutils.easter(holidaydate.year)  # Easter
        em = east + datetime.timedelta(1)  # Easter Monday
        return ddmm in Dateutils.__italian_holidays or datetime.date in (east, em)

    @staticmethod
    def is_weekend(weekenddate):
        return weekenddate.weekday() in (5, 6)

    @staticmethod
    def iter_month(year, month):
        d = datetime.date(year, month, 1)
        oneday = datetime.timedelta(1)
        while d.month == month:
            yield d
            d += oneday

    @staticmethod
    def check_timestamp(ts):
        return (ts is not None) and (ts > 0) and (ts < 2147483648000)

    @staticmethod
    def is_valid_timestamp(ts):
        return (ts is not None) and (ts > 0) and (ts < 2147483648000)

    @staticmethod
    def format_timestamp(ts, fmt="%H:%M:%S"):
        #  così ottengo le stringhe dalla stringa Trenitalia
        cts = Dateutils.convert_timestamp(ts)
        if cts is not None:
            return cts.strftime(fmt)
        return ''

    @staticmethod
    def convert_timestamp(ts):
        #  così ottengo i timestamp dalla stringa Trenitalia
        if Dateutils.check_timestamp(ts):
            return datetime.datetime.fromtimestamp(ts / 1000)
        else:
            return None

    @staticmethod
    def time_add(hours, minutes, deltamin):
        dt = datetime.datetime.combine(datetime.date.today(), datetime.time(hours, minutes)) + datetime.timedelta(
            minutes=deltamin)
        return dt.time()

    @staticmethod
    def time_addasdatetime(hours, minutes, deltamin):
        dt = datetime.datetime.combine(datetime.date.today(), datetime.time(hours, minutes)) + datetime.timedelta(
            minutes=deltamin)
        return dt

    @staticmethod
    def getdatimefromtimestring(tempogrezzo, onlytoday=True):
        try:
            tempogrezzo += datetime.datetime.now().strftime(' %Y-%m-%d')
            tempo = datetime.datetime.strptime(tempogrezzo, '%H:%M %Y-%m-%d')
            if not onlytoday and tempo < datetime.datetime.now():
                tempo = tempo + datetime.timedelta(days=1)
            return tempo
        except:
            logging.error('Exception raised [unknown]', exc_info=True)
            return None


class Datautils:
    __stationspath = os.path.join(os.path.dirname(__file__), 'data', 'stations.json')
    with open(__stationspath, 'r') as fp:
        __stations = json.load(fp)

    @staticmethod
    def stationfromid(stationid):
        return Datautils.__stations.get(stationid, 'UNKNOWN')

    @staticmethod
    def existsstationid(stationid):
        return stationid in Datautils.__stations

    @staticmethod
    def train_runs_on_date(train_info, traindate):
        # trainInfo['runs_on'] flag:
        # G    Runs every day
        # FER5 Runs only Monday to Friday (holidays excluded)
        # FER6 Runs only Monday to Saturday (holidays excluded)
        # FEST Runs only on Sunday and holidays
        runs_on = train_info.get('runs_on', 'G')
        suspended = train_info.get('suspended', [])

        for from_, to in suspended:
            ymd = traindate.strftime('%Y-%m-%d')
            if from_ <= ymd <= to:
                return False

        if runs_on == 'G':
            return True

        wd = datetime.date.weekday

        if runs_on == 'FEST':
            return Dateutils.is_holiday(traindate) or wd == 6

        if Dateutils.is_holiday(traindate):
            return False

        if runs_on == 'FER6' and wd < 6:
            return True
        if runs_on == 'FER5' and wd < 5:
            return True

        return False


# Copyright 2014 phoemur@gmail.com
# This work is free. You can redistribute it and/or modify it under the
# terms of the Do What The Fuck You Want To Public License, Version 2,
# as published by Sam Hocevar. See http://www.wtfpl.net/ for more details.

class IPgetter(object):
    '''
    This class is designed to fetch your external IP address from the internet.
    It is used mostly when behind a NAT.
    It picks your IP randomly from a serverlist to minimize request overhead
    on a single server
    '''

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.server_list = ['http://ip.dnsexit.com',
                            'http://ifconfig.me/ip',
                            'http://echoip.com',
                            'http://ipecho.net/plain',
                            'http://checkip.dyndns.org/plain',
                            'http://ipogre.com/linux.php',
                            'http://whatismyipaddress.com/',
                            'http://websiteipaddress.com/WhatIsMyIp',
                            'http://getmyipaddress.org/',
                            'http://www.my-ip-address.net/',
                            'http://myexternalip.com/raw',
                            'http://www.canyouseeme.org/',
                            'http://www.trackip.net/',
                            'http://icanhazip.com/',
                            'http://www.iplocation.net/',
                            'http://www.howtofindmyipaddress.com/',
                            'http://www.ipchicken.com/',
                            'http://whatsmyip.net/',
                            'http://www.ip-adress.com/',
                            'http://checkmyip.com/',
                            'http://www.tracemyip.org/',
                            'http://www.lawrencegoetz.com/programs/ipinfo/',
                            'http://www.findmyip.co/',
                            'http://ip-lookup.net/',
                            'http://www.dslreports.com/whois',
                            'http://www.mon-ip.com/en/my-ip/',
                            'http://www.myip.ru',
                            'http://ipgoat.com/',
                            'http://www.myipnumber.com/my-ip-address.asp',
                            'http://www.whatsmyipaddress.net/',
                            'http://formyip.com/',
                            'https://check.torproject.org/',
                            'http://www.displaymyip.com/',
                            'http://www.bobborst.com/tools/whatsmyip/',
                            'http://www.geoiptool.com/',
                            'https://www.whatsmydns.net/whats-my-ip-address.html',
                            'https://www.privateinternetaccess.com/pages/whats-my-ip/',
                            'http://checkip.dyndns.com/',
                            'http://myexternalip.com/',
                            'http://www.ip-adress.eu/',
                            'http://www.infosniper.net/',
                            'https://wtfismyip.com/text',
                            'http://ipinfo.io/',
                            'http://httpbin.org/ip',
                            'http://ip.ajn.me',
                            'https://diagnostic.opendns.com/myip',
                            'https://api.ipify.org']

    def get_externalip(self):
        '''
        This function gets your IP from a random server
        '''
        notyettryed = self.server_list.copy()
        myip = ''
        while len(notyettryed) > 0:
            server = random.choice(notyettryed)
            myip = self.fetch(server)
            if myip != '':
                self.logger.debug('server {0} returns {1}'.format(server,myip))
                break
            else:
                self.logger.debug('server {0} not working'.format(server))
                notyettryed.remove(server)
                continue
        return myip

    def fetch(self, server):
        """
        This function gets your IP from a specific server.
        """
        retvalue = ''
        url = None
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent',
                              "Mozilla/5.0 (X11; Linux x86_64; rv:24.0) Gecko/20100101 Firefox/24.0")]

        try:
            url = opener.open(server, timeout=2)
            content = url.read()

            # Didn't want to import chardet. Prefered to stick to stdlib

            try:
                content = content.decode('UTF-8')
            except UnicodeDecodeError:
                content = content.decode('ISO-8859-1')

            m = re.search(
                '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)',
                content)
            myip = m.group(0)
            if len(myip) > 0:
                retvalue = myip
        except Exception:
            self.logger.error('[main] Exception raised [unknown]', exc_info=True)
        finally:
            if url:
                url.close()

        return retvalue
