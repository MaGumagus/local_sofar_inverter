import requests
from requests.exceptions import HTTPError
from datetime import timedelta
import voluptuous as vol
import logging

from homeassistant.util import Throttle
from homeassistant.util.dt import parse_datetime
from homeassistant.components.sensor import PLATFORM_SCHEMA, ENTITY_ID_FORMAT
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_ELEVATION, CONF_SCAN_INTERVAL, ATTR_ATTRIBUTION
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import async_generate_entity_id
try:
    from homeassistant.components.sensor import SensorEntity
except ImportError:
    from homeassistant.components.sensor import SensorDevice as SensorEntity
from homeassistant.helpers.entity import async_generate_entity_id

DOMAIN = "local_sofar_inverter"
_LOGGER = logging.getLogger(__name__)
ATTRIBUTION = 'Information provided by Sofar inverter web page.'
DEFAULT_SCAN_INTERVAL = timedelta(minutes=5, seconds=0)
DEFAULT_MIN_ELEVATION = 5 # when no sun, no power, inverter is down

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DOMAIN): cv.string,
    vol.Optional(CONF_USERNAME, default='admin'): cv.string,
    vol.Optional(CONF_PASSWORD, default='admin'): cv.string,
    vol.Optional(CONF_ELEVATION, default=DEFAULT_MIN_ELEVATION): cv.positive_int,
    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period
})
HOST_PERFIX_ID = DOMAIN

def setup(hass, config):
    hass.states.set( DOMAIN, "Paulus")

    # Return boolean to indicate that initialization was successful.
    return True

TODAY_ENERGY_TAG = 'today_e'
INVERTER_ALARM_TAG = 'alarm'

INVERTER_DATA_VALUE_AT = 6
INVERTER_DATA = {
    'now_p':   ['power', 'Power now', 'mdi:solar-power', 'power', 'W', 'mesurement', '0'],
    'today_e': ['energy_today', 'Energy today', 'mdi:lightning-bolt', 'energy', 'kWh', 'total', '' ],
    'total_e': ['energy_total', 'Energy total', 'mdi:lightning-bolt', 'energy', 'kWh', 'total_increasing', '' ],
    'alarm':   ['alarm', 'Inverter alarms', 'mdi:solar-panel', 'None', '', '', '' ]
}
"""
var webdata_sn = "SA3ES233xxxxxx  ";
var webdata_msvn = "V310";
var webdata_ssvn = "";
var webdata_pv_type = "SA3ES233";
var webdata_rate_p = "3 00";
    webdata_now_p = "2790"; 
    webdata_today_e = "7.4";
    webdata_total_e = "8.0";
    webdata_alarm = "";
var webdata_utime = "0";
var cover_mid = "1797000000";
var cover_ver = "LSW3_15_FFFF_1.0.57";
var cover_wmode = "APSTA";
var cover_ap_ssid = "AP_1797000000";
var cover_ap_ip = "10.10.100.254";
var cover_ap_mac = "34:EA:AA:AA:AA:AA";
var cover_sta_ssid = "aaa";
var cover_sta_rssi = "78%";
var cover_sta_ip = "192.168.1687.199";
var cover_sta_mac = "34:EA:AA:AA:AA:AA";
var status_a = "1";
var status_b = "0";
var status_c = "0";
"""

"""
ID01, ID02, ID03, ID04
Problem po stronie sieci AC
Sprawdzić poprawność połączeń przewodów AC oraz zrobić pomiary napięcia, częstotliwości sieci, jeśli nie jest zgodne z normą - zgłosić do pogotowia energetycznego; istnieje możliwość ( za zgodą lokalnego operatora sieci energetycznej ) rozszerzenia zakresów parametrów sieci AC na falowniku - wypełnić formularz zgłoszeniowy i odesłać na serwis@soltec.pl
ID05
Napięcie wejściowe jak za niskie
Sprawdzić czy napięcie stringu nie jest mniejsze od minimalnego napięcia wejściowego falownika - dołożyć więcej paneli na string.
ID06
Zbyt niskie napięcie
Sprawdzić podłączenie inwertera do sieci. Upewnić się, że są załączone zabezpieczenia w rozdzielni
ID09
Napięcie wejściowe jest zbytwysokie
Sprawdzić czy napięcie stringu nie jest większe od maksymalnego napięcia wejściowego falownika. Jeśli tak, rozdzielić odpowiednio moduły na większą ilość stringów (sprawdzić czy nie zostanie przekroczona maksymalna wartość prądu wejściowego falownika)
ID10, ID11, ID71
Różna wartość natężeniawejściowego, Niewłaściwy tryb wejściowy
Sprawdzić ustawienia trybu wejściowego (czy jest równoległe czy niezależne)
ID12
Błąd prądu upływu GFCI
Jeśli usterka występuje sporadycznie, prawdopodobna przyczyna leży w chwilowym, nieprawidłowym działaniu sieci AC. Gdy problem ustąpi, status inwertera powróci do stanu prawidłowego.Jeśli usterka będzie występowała często i trwać będzie przez dłuższy czas, sprawdzić wartość rezystancji izolacji pomiędzy panelami PV a gruntem. Jeśli jest zbyt niska, sprawdź stan izolacji kabli fotowoltaicznych.
ID14
Natężenie prądu na wejściu jestzbyt wysokie – zadziałałozabezpieczenie sprzętowe
Sprawdzić czy natężenie prądu wejściowego nie jest wyższe niż to, które jest dopuszczalne dla inwerterów SOFAR. Sprawdzić okablowanie na wejściu inwertera. Jeśli wszystko jest w porządku skontaktuj się z serwisem.
ID15, ID16, ID17, ID18, ID19, ID20, ID21, ID22, ID23, ID24, ID26, ID27, ID29, ID49, ID50, ID51, ID52, ID53, ID54, ID55, ID65, ID66, ID67, ID68, ID69, ID70, ID74, ID75, ID76, ID77, ID95, ID96
Błąd wewnętrzny falownika
Przełączyć przełącznik DC na pozycję „OFF”, odczekać 5 minut. Następnie przełączyć przełącznik DC na pozycję „ON”. Sprawdzić czy usterka występuje nadal. Jeśli tak, wypełnić formularz zgłoszeniowy i odesłać na serwis@soltec.pl
ID25
Napięcie szyny jest za niskie
W momencie gdy konfiguracja paneli PV jest prawidłowa (błąd ID05 nie występuje), prawdopodobną przyczyną jest niedostateczne natężenie promieniowania słonecznego. W momencie gdy promieniowanie słoneczne osiągnie odpowiedni poziom, status inwertera powróci do stanu prawidłowego.
ID28
DCI jest zbyt wysoki
Sprawdzić ustawienia trybu wejściowego (czy jest równoległe czy niezależne). Jeśli ustawienia trybu wejściowego są prawidłowe, przełączyć przełącznik DC na pozycję „OFF”, odczekać 5 minut. Następnie przełączyć przełącznik DC na pozycję „ON”. Jeśli problem nie ustąpił, wypełnić formularz zgłoszeniowy i odesłać na serwis@soltec.pl
ID30
Zbyt wysokie natężenie prądu wejściowego
Sprawdzić czy natężenie prądu wejściowego nie jest wyższe niż to, które jest maksymalnie dopuszczalne dla inwerterów SOFAR, następnie sprawdzić okablowanie na wejściu inwertera. W przypadku gdy wszystko jest w normie, wypełnić formularz zgłoszeniowy i odesłać na serwis@soltec.pl
ID56
Rezystancja izolacji jest zbytniska.
Sprawdzić czy są dobrze zarobione złącza oraz czy nie są przetarte przewody po stronie DC, zrobić pomiar rezystancji izolacji po stronie DC, sprawdzić uziemienie falownika. Jeśli wszystko jest w normie, należy wypełnić formularz zgłoszeniowy i odesłać na serwis@soltec.pl
ID58, ID59, ID81
Temperatura inwertera jest zbyt wysoka / falownik obniżył swoją wydajność z powodu zbyt wysokiej temperatury
Upewnić się, że zamocowanie inwertera jest zgodne z wymaganiami zawartymi w instrukcji obsługi.Sprawdzić czy temperatura inwertera nie jest wyższa niż dopuszczalna maksymalna wartość. Jeślijest, postaraj się zapewnić lepszą wentylację w celu obniżenia temperatury inwertera.Sprawdzić czy wystąpiły błędy ID90-ID92 (błąd wentylatora). Jeśli tak, wówczas należy wymienićwentylator.
ID60
Nieprawidłowe uziemienie
Sprawdzić prawidłowość uziemienia.
ID82
Inwerter obniżył swojąwydajność z powodu zbytwysokiej częstotliwości sieci.
Gdy częstotliwość sieci jest zbyt wysoka, inwerter automatycznie redukuje swoją moc .
ID83
Inwerter obniżył swojąwydajność z powodu modułusterującego.
W przypadku obniżenia wydajności pracy, inwerter zapisuje parametr ID83. Sprawdź poprawność podłączenia przewodów pomiędzy wejściem i wyjściem portu sygnałowego w module komunikacyjnym.
ID84
Moduł kontrolny spowodowałwyłączenie inwertera.
W przypadku wyłączenia inwertera, inwerter zapisuje parametr ID84. Sprawdzić poprawność podłączenia przewodów pomiędzy wejściem i wyjściem portu sygnałowego w module komunikacyjnym.
ID94
Oprogramowanie pomiędzypanelem komunikacyjnym akontrolnym nie jest zgodne.
Wypełnić formularz zgłoszeniowy i odesłać na serwis@soltec.pl
ID97
Nieprawidłowo ustawiony kraj.
Sprawdzić ustawienia kraju zgodnie ze wskazówkami w instrukcji
ID98
Karta SD jest nieprawidłowa.
Zamienić kartę SD.
"""
INVERTER_ALARM_CODES = {
    '01': ['GridOVP','The power grid voltage is too high'],
    '02': ['GridUVP','The power grid voltage is too low'],
    '03': ['GridOFP','The power grid frequency is too high'],
    '04': ['GridUFP','The power grid frequency is too low'],
    '12': ['GFCIFault','GFCIFault'],
    '14': ['HwBoostOCP','The input current is too high, and has happen hardware protection']
}

def InverterAlarmDecode( v1 ):
    _LOGGER.debug('InverterAlarmDecode')
    v2 = v1 + ': ';
    for error_id in INVERTER_ALARM_CODES:
        if( v1.find(error_id) > 0 ):
            v2 += ( INVERTER_ALARM_CODES[error_id][0] ) + ' '
            ## max  255 v2 += ( INVERTER_ALARM_CODES[error_id][0] + INVERTER_ALARM_CODES[error_id][1] )
    return v2;

#[custom_components.local_sofar_inverter.sensor] today_e=5.88
#[custom_components.local_sofar_inverter.sensor] today_e=6.0
#[custom_components.local_sofar_inverter.sensor] today_e=6.5
#[custom_components.local_sofar_inverter.sensor] today_e=6.9    -- INVERTER WRONG FORMATING 
#[custom_components.local_sofar_inverter.sensor] today_e=6.13   -- INVERTER WRONG FORMATING 
#[custom_components.local_sofar_inverter.sensor] today_e=6.19
def FixSofarData( v1 ):
    v2 = v1[v1.find('.')+1:len(v1)]
    if (len(v2) == 1 ):
        _LOGGER.debug('FixData')
        return v1.replace('.','.0')
    else:
        return v1

def GetValueForTag(txt,tag):
    pos = txt.find( 'webdata_' + tag )
    t1 = txt[pos:pos+35]
    p1 = t1.find('=');
    p2 = t1.find(';');
    t2 = t1[p1+1:p2-1]
    t = t2.replace(' ','').replace('"','')
    _LOGGER.debug( tag + '=' + t ) 
    return t

class SofarNetSensor(SensorEntity):
    def __init__(self, entity_id, name, updater):
        #_LOGGER.debug('SofarNetSensor.__init__')
        self.entity_id = entity_id
        self._name = name
        self._updater = updater
        self._data = None

    @property
    def device_state_attributes(self):
        _LOGGER.debug('SofarNetSensor.device_state_attributes')
        output = dict()
        output[ATTR_ATTRIBUTION] = ATTRIBUTION
        return output

    async def async_update(self):
        await self._updater.async_update()

class SofarNetDataSensor(SofarNetSensor):
    def __init__(self, entity_id, name, updater, data_type):
        #_LOGGER.debug('SofarNetDataSensor.__init__')
        super().__init__(entity_id, name, updater)
        self._entity_id = entity_id
        self._data_type = data_type
        self._data_key = INVERTER_DATA[self._data_type][0]
        self._state = None
        self._data_from_inverter = updater.inverter_retrived_data

    @property
    def is_on(self):
        _LOGGER.debug('SofarNetDataSensor.is_on')
        data = self._updater.data_from_inverter
        return data is not None and data[self._data_key] > 0

    @property
    def device_state_attributes(self):
        _LOGGER.debug('SofarNetDataSensor.device_state_attributes')
        output = super().device_state_attributes
        if self.is_on:
            _LOGGER.debug('SofarNetDataSensor.device_state_attributes.is_on')
            data = self._updater.data_from_inverter
            output['value'] = GetValueForTag(data.text,self._data_type)
            #output['level'] = data[self._data_key]
            #output['description'] = INVERTER_DATA[self._data_type][data[self._data_key]]
        return output

    @property
    def state(self):
        #_LOGGER.debug('SofarNetDataSensor.state' + self._data_type)
        #self._state = GetValueForTag(self._data_from_inverter.text,self._data_type)
        self._state = INVERTER_DATA[self._data_type][INVERTER_DATA_VALUE_AT]
        #_LOGGER.debug(self._data_type + '=' + self._state)
        return self._state

    @property
    def icon(self):
        return INVERTER_DATA[self._data_type][2]

    @property
    def name(self) -> str:
        return self._name + INVERTER_DATA[self._data_type][1]
        
    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return HOST_PERFIX_ID+'_'+self._data_type

    @property
    def device_class(self):
        return INVERTER_DATA[self._data_type][3]

    @property
    def state_class(self):
        return INVERTER_DATA[self._data_type][5]

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return INVERTER_DATA[self._data_type][4]

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    name = config.get(CONF_NAME)
    scan_interval = config.get(CONF_SCAN_INTERVAL)
    host = config.get(CONF_HOST)
    usr  = config.get(CONF_USERNAME)
    pwd  = config.get(CONF_PASSWORD)
    min_elevation = config.get(CONF_ELEVATION)
    _LOGGER.debug('inverter host:' + host ) 
    sensors = []
    sensor_name = '{} - '.format(name)
    url = 'http://' + usr + ':' + pwd + '@' + host + '/status.html'
    updater = SofarNetDataUpdater(hass, url, scan_interval, min_elevation)
    await updater.async_update()
    for data_type in INVERTER_DATA:
        uid = '{}_{}'.format(name, data_type)
        entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, uid, hass=hass)
        #_LOGGER.debug(uid)
        #_LOGGER.debug(entity_id)
        #_LOGGER.debug(sensor_name)
        sensors.append(SofarNetDataSensor(entity_id, sensor_name, updater, data_type))
    async_add_entities(sensors, True)


class SofarNetDataUpdater:
    def __init__(self, hass, url, scan_interval, min_elevation):
        #_LOGGER.debug('SofarNetDataUpdater.__init__')
        self._hass = hass
        self._url = url
        self._min_elevation = min_elevation
        self.async_update = Throttle(scan_interval)(self._async_update)
        self.data_from_inverter = None
        
    @property
    def inverter_retrived_data(self):
        #_LOGGER.debug('SofarNetDataUpdater.data_from_inverter')
        return self.data_from_inverter

    async def _async_update(self):
        await self._hass.async_add_executor_job(self._update_data)

    def _update_data(self):
        #_LOGGER.debug('SofarNetDataUpdater._update_data')
        data_from_inverter = ''
        elevation = 90
        try:
            _sun = self._hass.states.get('sun.sun')
            #_LOGGER.debug(_sun)
            elevation =  _sun.attributes.get('elevation')
        except Exception as err:
            _LOGGER.error(f'Other error occurred: {err}')        

        _LOGGER.debug(f'Current sun elevation: {elevation} > min {self._min_elevation}?')        
        if elevation > self._min_elevation:
            try:
                _LOGGER.debug(self._url)
                data_from_inverter = requests.get(self._url)
                # If the response was successful, no Exception will be raised
                data_from_inverter.raise_for_status()
                for data_type in INVERTER_DATA:
                    INVERTER_DATA[data_type][INVERTER_DATA_VALUE_AT] = GetValueForTag(data_from_inverter.text,data_type)
                    if data_type == TODAY_ENERGY_TAG:
                        INVERTER_DATA[data_type][INVERTER_DATA_VALUE_AT] = FixSofarData( INVERTER_DATA[data_type][INVERTER_DATA_VALUE_AT] )
                    #if data_type == INVERTER_ALARM_TAG:                             # for testing
                    #    INVERTER_DATA[data_type][INVERTER_DATA_VALUE_AT] = 'F12F14' # for testing
                    if data_type == INVERTER_ALARM_TAG and len( INVERTER_DATA[data_type][INVERTER_DATA_VALUE_AT] ) > 0:
                        INVERTER_DATA[data_type][INVERTER_DATA_VALUE_AT] = InverterAlarmDecode( INVERTER_DATA[data_type][INVERTER_DATA_VALUE_AT] )
            except HTTPError as http_err:
                _LOGGER.error(f'HTTP error occurred: {http_err}') 
            except HTTPConnectionPool as http_err:
                _LOGGER.error(f'HTTP connection error occurred: {http_err}') 
            except Exception as err:
                _LOGGER.error(f'Other error occurred: {err}')
            else:
                _LOGGER.debug('Got data from the inverter!')