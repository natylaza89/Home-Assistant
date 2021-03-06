"""
Support for scanning a network with arp-scan.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/device_tracker.arpscan_tracker/
"""
import logging
import re
import subprocess
from collections import namedtuple
from datetime import timedelta
 
import voluptuous as vol
 
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
from homeassistant.components.device_tracker import (
    DOMAIN, PLATFORM_SCHEMA, DeviceScanner)
from homeassistant.util import Throttle
 
_LOGGER = logging.getLogger(__name__)
 
CONF_EXCLUDE = 'exclude'
CONF_OPTIONS = 'scan_options'
DEFAULT_OPTIONS = '-l -g -t1 -q'
 
MIN_TIME_BETWEEN_SCANS = timedelta(seconds=5)
 
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_EXCLUDE, default=[]):
        vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_OPTIONS, default=DEFAULT_OPTIONS):
        cv.string
})
 
 
def get_scanner(hass, config):
    """Validate the configuration and return a ArpScan scanner."""
    scanner = ArpScanDeviceScanner(config[DOMAIN])
 
    return scanner if scanner.success_init else None
 
 
Device = namedtuple('Device', ['mac', 'name', 'ip', 'last_update'])
 
 
class ArpScanDeviceScanner(DeviceScanner):
    """This class scans for devices using arp-scan."""
 
    exclude = []
 
    def __init__(self, config):
        """Initialize the scanner."""
        self.last_results = []
 
        self.exclude = config[CONF_EXCLUDE]
        self._options = config[CONF_OPTIONS]
 
        self.success_init = self._update_info()
        _LOGGER.debug("Init called")
 
    def scan_devices(self):
        """Scan for new devices and return a list with found device IDs."""
        self._update_info()
 
        _LOGGER.debug("Scan devices called")
        return [device.mac for device in self.last_results]
 
    def get_device_name(self, mac):
        """Return the name of the given device or None if we don't know."""
        filter_named = [device.name for device in self.last_results
                        if device.mac == mac]
 
        if filter_named:
            _LOGGER.debug("Filter named called")
            return filter_named[0]
        else:
            return None
 
    @Throttle(MIN_TIME_BETWEEN_SCANS)
    def _update_info(self):
        """Scan the network for devices.
       Returns boolean if scanning successful.
       """
        _LOGGER.debug("Update_info called")
 
        options = self._options
 
        last_results = []
        exclude_hosts = self.exclude
 
        scandata = subprocess.getoutput("arp-scan --interface=enx30f7d704c59e --localnet")
 
        now = dt_util.now()
        for line in scandata.splitlines():
            ipv4 = re.findall(r'[0-9]+(?:\.[0-9]+){3}', line)
            if not ipv4:
                continue
 
            parts = line.split()
            ipv4 = parts[0]
            for exclude in exclude_hosts:
                if exclude == ipv4:
                    _LOGGER.debug("Excluded %s", exclude)
                    continue
 
            name = ipv4
            mac = parts[1]
            last_results.append(Device(mac, name, ipv4, now))
 
        self.last_results = last_results
 
        _LOGGER.debug("Update_info successful")
        return True