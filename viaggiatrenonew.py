import logging
import json
import re
import urllib.parse
from urllib.request import urlopen

FORMAT = '[%(levelname)s] (%(threadName)-9s) %(message)s'
logging.basicConfig(format=FORMAT)


# Decoders for API Output - TODO: Proper error handling
def _decode_json(s):
    try:
        if s == '':
            logging.info('json decode a <null> string, return None')
            return None
        return json.loads(s)
    except:
        logging.error('Exception raised [unknown]', exc_info=True)
        return None


def _decode_lines(s, linefunc):
    try:
        if s == '':
            logging.info('json decode a <null> string, return None')
            return []

        lines = s.strip().split('\n')
        result = []
        for line in lines:
            result.append(linefunc(line))

        return result
    except:
        logging.error('Exception raised [unknown]', exc_info=True)
        return None


def _decode_cercanumerotrenotrenoautocomplete(s):
    def linefunc(line):
        r = re.search('^(\d+)\s-\s(.+)\|(\d+)-(.+)$', line)
        if r is not None:
            return r.group(2, 4)

    return _decode_lines(s, linefunc)


def _decode_autocompletastazione(s):
    return _decode_lines(s, lambda line: tuple(line.strip().split('|')))


class Viaggiatrenonew:
    def __init__(self, **options):
        self._urlbase = 'http://www.viaggiatreno.it/viaggiatrenonew/resteasy/viaggiatreno/'
        self.__verbose = options.get('verbose', False)
        self.__urlopen = options.get('urlopen', urlopen)
        self.__plainoutput = options.get('plainoutput', False)
        self.__decoders = {
            'andamentoTreno': _decode_json,
            'cercaStazione': _decode_json,
            'tratteCanvas': _decode_json,
            'dettaglioStazione': _decode_json,
            'regione': _decode_json,
            'arrivi': _decode_json,
            'partenze': _decode_json,
            'soluzioniViaggioNew': _decode_json,
            'cercaNumeroTrenoTrenoAutocomplete': _decode_cercanumerotrenotrenoautocomplete,
            'autocompletaStazione': _decode_autocompletastazione
        }
        self.__default_decoder = lambda x: x
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    @property
    def urlbase(self):
        return self._urlbase

    def __checkanddecode(self, function, data):
        decoder = self.__decoders.get(function, self.__default_decoder)
        return decoder(data)

    def call(self, function, *params, **options):
        plain = options.get('plainoutput', self.__plainoutput)
        verbose = options.get('verbose', self.__verbose)
        try:
            queryparam = '/'.join(urllib.parse.quote(str(p), safe='') for p in params)
            url = self._urlbase + function + '/' + queryparam
            self.logger.debug(url)
            req = self.__urlopen(url)
            data = req.read().decode('utf-8')
            if plain:
                return data
            else:
                return self.__checkanddecode(function, data)
        except:
            self.logger.error('Exception raised [unknown]', exc_info=True)
            return None
