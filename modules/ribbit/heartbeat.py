import time
import logging
import uasyncio as asyncio

from machine import WDT

class Heartbeat:
    def __init__(self, in_simulator, is_sd):
        self._in_simulator = in_simulator
        self._logger = logging.getLogger(__name__)
        self._is_sd = is_sd


        if not self._in_simulator:
            self._setup_pixel()
            asyncio.create_task(self._loop())

    def _setup_pixel(self):
        import neopixel
        import machine

        #machine.Pin(21, machine.Pin.OUT, value=1)
        neo_ctrl = machine.Pin(48, machine.Pin.OUT)
        self.led_ctrl = machine.Pin(14, machine.Pin.OUT)
        self._pixel = neopixel.NeoPixel(neo_ctrl, 1)

    async def _loop(self):
        interval = 2000
        sd_interval = 300
        warn_interval = 3000 

        on = True
        px = self._pixel

        while True:
            if not self._in_simulator:
                if on:
                    px[0] = (0, 192, 0)
                    self.led_ctrl.on()
                else:
                    px[0] = (0, 0, 0)
                    self.led_ctrl.off()
                on = not on
                px.write()

            start = time.ticks_ms()
            if self._is_sd:
                await asyncio.sleep_ms(sd_interval)
            else:
                await asyncio.sleep_ms(interval)

            duration = time.ticks_diff(time.ticks_ms(), start)

            if duration > warn_interval:
                self._logger.warning(
                    "Event loop blocked for %d ms", duration - interval
                )
