from ribbit.utils.time import isotime
import time
import logging
import uasyncio as asyncio
import collections
import json

import ribbit.coap as _coap
from machine import WDT

class SensorAggregator:
    def __init__(self, registry):
        self._logger = logging.getLogger(__name__)
        self._registry = registry
        # WDT for autoreboot
        self._wdt = WDT(id=0,timeout=180000)
        self._wdt.feed()
        asyncio.create_task(self._loop())


    async def _loop(self):
        while True:
            # Send a data point every 5 seconds
            if self._registry.is_sd_card:
                await asyncio.sleep_ms(60000)
            else:
                await asyncio.sleep_ms(5000)
            

            ret = collections.OrderedDict()
            good_temp = None
            for sensor in self._registry.sensors.values():
                if sensor.config.name == "dps310":
                    ret[sensor.config.name] = {
                        "temperature": sensor.temperature,
                        "pressure": sensor.pressure,
                        "t": isotime(sensor.last_update),
                    }
                    good_temp = sensor.temperature

                elif sensor.config.name == "scd30":
                    ret[sensor.config.name] = {
                        "temperature": sensor.temperature,
                        "co2": sensor.co2,
                        "humidity": sensor.humidity,
                        "t": isotime(sensor.last_update),
                    }
                elif sensor.config.name == "gps":
                    ret[sensor.config.name] = {
                        "has_fix": sensor.has_fix,
                        "latitude": sensor.latitude,
                        "longitude": sensor.longitude,
                        "altitude": sensor.altitude,
                        "t": isotime(sensor.last_update),
                    }
                elif sensor.config.name == "memory":
                    ret[sensor.config.name] = {
                        "allocated": sensor.allocated,
                        "free": sensor.free,
                    }

            if good_temp != None:
                ret["scd30"]["temperature"] = good_temp
                
            self._logger.info("Aggregated Data: %s", json.dumps(ret))
            
            
            if self._registry.is_sd_card:
                try:
                    fl = open('/sdcard/frogdata.txt', 'a')
                    try:
                        n = fl.write(f'{ret["gps"]["t"]};{ret["scd30"]["temperature"]};{ret["dps310"]["pressure"]};{ret["scd30"]["humidity"]};{ret["scd30"]["co2"]};{ret["gps"]["latitude"]};{ret["gps"]["longitude"]};{ret["gps"]["altitude"]}\n')
                        print(f'{n} bytes written')
                        self._wdt.feed()
                        fl.close()
                    except OSError:
                        self._logger.warn('Cannot write data to SD file')

                except OSError:
                    self._logger.warn('Cannot open file on SD')
            
            try:
                coap = self._registry.golioth._coap
                await coap.post(
                    ".s/" + "ribbitnetwork.datapoint",
                    json.dumps(ret),
                    format=_coap.CONTENT_FORMAT_APPLICATION_JSON)
                # self._logger.info("WDT feeded")
                self._wdt.feed()

            except Exception:
                pass

            

