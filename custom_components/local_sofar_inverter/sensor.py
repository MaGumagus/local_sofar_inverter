from .const import DOMAIN
import logging
import requests
from requests.exceptions import HTTPError
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity, async_generate_entity_id
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_ELEVATION, CONF_SCAN_INTERVAL, ATTR_ATTRIBUTION
from homeassistant.components.sensor import PLATFORM_SCHEMA, ENTITY_ID_FORMAT
from homeassistant.util import Throttle
from datetime import timedelta

try:
    from homeassistant.components.sensor import SensorEntity
except ImportError:
    from homeassistant.components.sensor import SensorDevice as SensorEntity

_LOGGER = logging.getLogger(__name__)

#PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
#    vol.Required(CONF_HOST): cv.string,
#    vol.Optional(CONF_NAME, default=DOMAIN): cv.string,
#    vol.Optional(CONF_USERNAME, default='admin'): cv.string,
#    vol.Optional(CONF_PASSWORD, default='admin'): cv.string,
#    vol.Optional(CONF_ELEVATION, default=DEFAULT_MIN_ELEVATION): cv.positive_int,
#    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period
#})

TODAY_ENERGY_TAG = 'today_e'
POWER_NOW_TAG = 'now_p'
INVERTER_ALARM_TAG = 'alarm'
INVERTER_TYPE_TAG = 'pv_type'
INVERTER_SN_TAG = 'sn'

WEB_PREFIX = "webdata_"
INVERTER_DATA_VALUE_AT = 6
INVERTER_DATA = {
    'now_p':   ['power', 'PV power now', 'mdi:solar-power', 'power', 'W', 'mesurement', '0'],
    'today_e': ['energy_today', 'PV energy today', 'mdi:lightning-bolt', 'energy', 'kWh', 'total', '0' ],
    'total_e': ['energy_total', 'PV energy total', 'mdi:lightning-bolt', 'energy', 'kWh', 'total_increasing', '' ],
    'alarm':   ['alarm', 'Inverter alarms', 'mdi:solar-panel', 'None', '', '', '' ],
    'pv_type': ['type', 'PV type', 'mdi:solar-panel', 'None', '', '', '' ],
    'sn':      ['sn', 'SN', 'mdi:solar-panel', 'None', '', '', '' ]
}
inverter_url = "https://google.com"

async def async_setup_entry(hass, config_entry, async_add_entities):
    name = config_entry.data[CONF_NAME]
    host = config_entry.data[CONF_HOST]
    usr  = config_entry.data[CONF_USERNAME]
    pwd  = config_entry.data[CONF_PASSWORD]
    url = 'http://' + usr + ':' + pwd + '@' + host + '/status.html'
    _LOGGER.info('inverter host: ' + url ) 
    min_elevation = config_entry.data[CONF_ELEVATION]
    _LOGGER.info('CONF_ELEVATION: ' + str(min_elevation) ) 
    #scan_interval = config_entry.data[CONF_SCAN_INTERVAL]
    scan_interval = timedelta(minutes=0, seconds=config_entry.data[CONF_SCAN_INTERVAL])
    _LOGGER.info('inverter SCAN_INTERVAL: ' + str(scan_interval) ) 
    sensors = []
    sensor_name = '{}_'.format(name)
    updater = SofarNetDataUpdater(hass, url, scan_interval, min_elevation)
    await updater.async_update()
    for data_type in INVERTER_DATA:
        uid = '{}_{}'.format(name, data_type)
        entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, uid, hass=hass)
        _LOGGER.debug(uid)
        #_LOGGER.debug(entity_id)
        #_LOGGER.debug(sensor_name)
        sensors.append(SofarNetDataSensor(name, uid, entity_id, sensor_name, updater, data_type))
    async_add_entities(sensors, True)

INVERTER_ALARM_CODES = {
    '01': ['GridOVP','The power grid voltage is too high'],
    '02': ['GridUVP','The power grid voltage is too low'],
    '03': ['GridOFP','The power grid frequency is too high'],
    '04': ['GridUFP','The power grid frequency is too low'],
    '12': ['GFCIFault','GFCIFault'],
    '14': ['HwBoostOCP','The input current is too high, and has happen hardware protection']
}

def InverterAlarmDecode( v1 ):
    #_LOGGER.debug('InverterAlarmDecode')
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
    pos = txt.find( WEB_PREFIX + tag )
    t1 = txt[pos:pos+35]
    p1 = t1.find('=');
    p2 = t1.find(';');
    t2 = t1[p1+1:p2-1]
    t = t2.replace(' ','').replace('"','')
    #_LOGGER.debug( tag + '=' + t ) 
    return t

class SofarNetSensor(SensorEntity):
    def __init__(self, entity_id, name, updater):
        _LOGGER.debug('SofarNetSensor')
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
    def __init__(self, name, uid, entity_id, sensor_name, updater, data_type):
        super().__init__(entity_id, name, updater)
        self._name = name
        self._uid = uid
        self._entity_id = entity_id
        self._sensor_name = sensor_name
        self._data_type = data_type
        self._data_key = INVERTER_DATA[self._data_type][0]
        self._state = 0
        #self._state = None
        self._data_from_inverter = updater.inverter_retrived_data

    @property
    def is_on(self):
        _LOGGER.debug('SofarNetDataSensor.is_on')
        data = self._updater.data_from_inverter
        return data is not None and data[self._data_key] > 0

    @property
    def device_info(self):
        return {
             "identifiers": {(DOMAIN, self._name)},
             "name": self._name,
             "manufacturer": "Sofar",
             "model": INVERTER_DATA[INVERTER_TYPE_TAG][INVERTER_DATA_VALUE_AT],
             "hw_version": INVERTER_DATA[INVERTER_SN_TAG][INVERTER_DATA_VALUE_AT],
             "via_device": None,
             "configuration_url": inverter_url
         }
    
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
        #_LOGGER.debug('SofarNetDataSensor.state ' + self._data_type)
        #self._state = GetValueForTag(self._data_from_inverter.text,self._data_type)
        self._state = INVERTER_DATA[self._data_type][INVERTER_DATA_VALUE_AT]
        _LOGGER.debug('{}= {}'.format(self._data_type, self._state))
        return self._state

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
#        return HOST_PERFIX_ID+'_'+self._data_type
        return self._uid

    @property
    def name(self) -> str:
#        return self._name + INVERTER_DATA[self._data_type][1]
        return INVERTER_DATA[self._data_type][1]
        
    @property
    def icon(self):
        return INVERTER_DATA[self._data_type][2]

    @property
    def device_class(self):
        return INVERTER_DATA[self._data_type][3]

    @property
    def unit_of_measurement(self):
        return INVERTER_DATA[self._data_type][4]

    @property
    def state_class(self):
        return INVERTER_DATA[self._data_type][5]

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    name = config.get(CONF_NAME)
    scan_interval = config.get(CONF_SCAN_INTERVAL)
    host = config.get(CONF_HOST)
    usr  = config.get(CONF_USERNAME)
    pwd  = config.get(CONF_PASSWORD)
    min_elevation = config.get(CONF_ELEVATION)
    _LOGGER.debug('async_setup_platform inverter host:' + host ) 
    sensors = []
    sensor_name = '{} - '.format(name)
    inverter_url = 'http://' + usr + ':' + pwd + '@' + host
    url = inverter_url + '/status.html'
    updater = SofarNetDataUpdater(hass, url, scan_interval, min_elevation)
    await updater.async_update()
"""     for data_type in INVERTER_DATA:
        uid = '{}_{}'.format(name, data_type)
        entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, uid, hass=hass)
        _LOGGER.debug(uid)
        _LOGGER.debug(entity_id)
        #_LOGGER.debug(sensor_name)
        sensors.append(SofarNetDataSensor(name, entity_id, sensor_name, updater, data_type))
    async_add_entities(sensors, True) """

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
        _LOGGER.debug('SofarNetDataUpdater.data_from_inverter')
        return self.data_from_inverter

    async def _async_update(self):
        await self._hass.async_add_executor_job(self._update_data)

    def _update_data(self):
        #_LOGGER.debug('SofarNetDataUpdater._update_data')
        data_from_inverter = ''
        elevation = 90
        sun_rising = True
        try:
            _sun = self._hass.states.get('sun.sun')
            elevation =  _sun.attributes.get('elevation')
            sun_rising =  _sun.attributes.get('rising')
        except Exception as err:
            _LOGGER.error(f'Other error occurred: {err}')        

        if elevation <= self._min_elevation:
            _LOGGER.debug(f'Current sun elevation: {elevation} > min {self._min_elevation}?')        
            INVERTER_DATA[POWER_NOW_TAG][INVERTER_DATA_VALUE_AT] = 0.0
            if sun_rising:
               _LOGGER.debug(f'Sun rising: {sun_rising} elevation: {elevation} > min {self._min_elevation}?')        
               INVERTER_DATA[TODAY_ENERGY_TAG][INVERTER_DATA_VALUE_AT] = 0.0
        if elevation > self._min_elevation:
            try:
                _LOGGER.info(self._url)
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
#            except HTTPConnectionPool as http_err:
#                _LOGGER.error(f'HTTP connection error occurred: {http_err}') 
            except Exception as err:
                _LOGGER.error(f'Other error occurred: {err}')
            else:
                _LOGGER.info('Got data from the inverter')
                #_LOGGER.debug(data_from_inverter.text)            

                