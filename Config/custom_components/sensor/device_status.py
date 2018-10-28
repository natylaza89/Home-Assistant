"""////////////////////////////////////////////////////////////////////////////////////////////////
This sensor checks the status of network objects such as Computers, Routers, Servers, Esp8266 based sensors, Smart TV and more
The sensor is checking the object status by using fping commans wich needs to be installs.
to install fping, run the fallowing command:
sudo apt-get install fping --yes
Date: 26/04/2018
Author: Tomer Klein
Many thanks to Tomer Figenblat (https://github.com/TomerFi) for all the help.
installation notes:
place this file in the following folder and restart home assistant:
/config/custom_components/sensor or /home/homeassistant/.homeassistant/custom_components/sensor
yaml configuration example:
sensor:
  - platform: device_status
    scan_interval: 10
    devices:
    internet_connection:
       host: 8.8.8.8 8
       name: "Internet Connection"
    
////////////////////////////////////////////////////////////////////////////////////////////////"""
import datetime
import logging
import re
import subprocess
import voluptuous as vol
from homeassistant.helpers.entity import Entity, generate_entity_id 
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import DOMAIN, PLATFORM_SCHEMA 
from homeassistant.const import (CONF_HOST, CONF_NAME, CONF_SCAN_INTERVAL, CONF_ICON, CONF_DEVICES)


REQUIREMENTS = []
DEPENDENCIES = []
_LOGGER = logging.getLogger(__name__)
#DEFAULT_NAME = 'Check Status' # 
SCAN_INTERVAL_DEFAULT = datetime.timedelta(seconds=10)
DEFAULT_ICON = "mdi:desktop-classic"
#DOMAIN = "sensor" # 
PLATFORM_NAME = "device_status"
ENTITY_ID_FORMAT = DOMAIN + '.' + PLATFORM_NAME + '_{}'

DEVICE_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME): cv.string,
    vol.Required(CONF_ICON, default=DEFAULT_ICON): cv.icon 
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL_DEFAULT): cv.positive_timedelta,
    vol.Required(CONF_DEVICES):
        vol.Schema({cv.slug: DEVICE_SCHEMA})
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    
    scan_interval = config.get(CONF_SCAN_INTERVAL) 
    devices = config.get(CONF_DEVICES)

    entities = []

    for slug_id, config in devices.items():
        name = config.get(CONF_NAME, None)
        host = config.get(CONF_HOST)
        icon = config.get(CONF_ICON)
        
        device = CHECK_STATUS(slug_id, hass, name, host, icon)

        entities.append(device)

    add_devices(entities, True)
    return True

def get_device_status(host):
    p = subprocess.Popen("fping -C1 -q "+ host +"  2>&1 | grep -v '-' | wc -l", stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    p_status = p.wait()
    status = re.findall('\d+', str(output))[0]
    if status=="1":
        return 'online'
    else:
        return 'offline'

class CHECK_STATUS(Entity):
    """representation of the sensor entity"""
    def __init__(self, slug_id, hass, name, host, icon):
        """initialize the sensor entity"""
        self.entity_id = generate_entity_id(ENTITY_ID_FORMAT, slug_id, hass=hass)
        self.hass = hass
        self._name = name
        self._host = host
        self._icon = icon 
        self._state = get_device_status(host)
        

    @property
    def name(self):
        """friendly name"""
        return self._name

    @property
    def host(self):
        """host"""
        return self._host

    @property
    def should_poll(self):
        """entity should not be polled for updates"""
        return True

    @property
    def state(self):
        """sensor state"""
        return self._state

    @property
    def icon(self):
        """sensor icon"""
        if self._state == 'online':
            return 'mdi:arrow-up-bold-circle-outline'
        else:
            return 'mdi:arrow-down-bold-circle-outline'
            
        return self._icon
     
    def update(self):
        """handling state updates"""
        self._state = get_device_status(self._host)