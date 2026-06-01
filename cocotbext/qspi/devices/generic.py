# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2021 Spencer Chang
# Transmits the previously received word on the next transaction
from collections import deque

from cocotb.triggers import First

from ..exceptions import QSpiFrameError
from ..qspi import QSpiBus, QSpiConfig, QSpiSubordinateBase, reverse_word


class QSpiSubordinateLoopback(QSpiSubordinateBase):
    """ Does not loopback in quad mode!
    Probably put it into another class or something...
    """
    def __init__(self, bus: QSpiBus, config: QSpiConfig):
        self._config = config

        self._out_queue = deque()
        self._out_queue.append(0)

        super().__init__(bus)

    async def get_contents(self):
        await self.idle.wait()
        if self._config.msb_first:
            return self._out_queue[0]
        else:
            return reverse_word(self._out_queue[0], self._config.word_width)

    async def _transaction(self, frame_start, frame_end):
        await frame_start
        self.idle.clear()

        # we do not have to reverse the word based on msb or lsb since we are just looping back
        if not self._config.is_quad_mode:
            tx_word = self._out_queue.popleft()
            if not self._config.cpha:
                # when CPHA=0, we use the chip select edge (frame start) to propagate data.
                self._miso_d0.value = bool(tx_word & (1 << self._config.word_width - 1))
                # now we can do the sclk cycles, but we do one less (because we don't have all the words
                content = int(await self._shift(self._config.word_width - 1, tx_word=tx_word))

                # get the last data bit
                r = await First(self._sclk.value_change, frame_end)
                content = (content << 1) | int(self._mosi_d1.value)

                # check to make sure we didn't lose the frame
                if r == frame_end:
                    raise QSpiFrameError("End of frame before last bit was sampled")
            else:
                content = int(await self._shift(self._config.word_width, tx_word=tx_word))
        else:
            if not self._config.cpha:
                # now we can do the sclk cycles, but we do one less (because we don't have all the words
                content = int(await self._quad_recieve(self._config.word_width - 4))

                # get the last 4 data bit
                r = await First(self._sclk.value_change, frame_end)
                content |= int(self._miso_d0.value) << 3
                content |= int(self._mosi_d1.value) << 2
                content |= int(self._d2.value)      << 1
                content |= int(self._d3.value)      << 0

                # check to make sure we didn't lose the frame
                if r == frame_end:
                    raise QSpiFrameError("End of frame before last bit was sampled")
            else:
                content = int(await self._quad_recieve(self._config.word_width))

        await frame_end
        self._out_queue.append(content)
