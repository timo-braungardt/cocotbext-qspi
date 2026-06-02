"""
Simulation model for S25HS256T / S25HS512T / S25HS01GT / S25HL256T / S25HL512T / S25HL01GT
"""

from collections import deque

from cocotb.triggers import FallingEdge
from cocotb.triggers import First
from cocotb.triggers import RisingEdge

from ...exceptions import QSpiFrameError
from ...qspi import QSpiBus
from ...qspi import QSpiConfig
from ...qspi import QSpiSubordinateBase


class S25HS256T(QSpiSubordinateBase):
    _config = QSpiConfig(
        word_width=8,
        cpol=False,
        cpha=False,
        msb_first=True,
        frame_spacing_ns=6,
        cs_active_low=True,
        is_quad_mode=False,
    )


    def __init__(self, bus: QSpiBus):
        self._out_queue = deque()
        self._out_queue.append(0)
        self._opcode = -1
        self._address = -1
        super().__init__(bus)


    async def _recieve_bits(self, num_bits, frame_end, quad_mode=False):
        if not quad_mode:
            tx_word = 0     # ToDo: in spi mode, it should shift out the current data in the register
            if not self._config.cpha:
                content = int(await self._shift(num_bits - 1, tx_word=tx_word))
                # get the last data bit
                r = await First(self._sclk.value_change, frame_end)
                content = (content << 1) | int(self._mosi_d1.value)
                if r == frame_end:
                    raise QSpiFrameError("End of frame before last bit was sampled")
            else:
                content = int(await self._shift(num_bits, tx_word=tx_word))
        else:
            if not self._config.cpha:
                content = int(await self._quad_recieve(num_bits - 4))
                r = await First(self._sclk.value_change, frame_end)
                # get the last 4 data bit
                content |= int(self._miso_d0.value) << 0
                content |= int(self._mosi_d1.value) << 1
                content |= int(self._d2.value)      << 2
                content |= int(self._d3.value)      << 3
                if r == frame_end:
                    raise QSpiFrameError("End of frame before last bit was sampled")
            else:
                content = int(await self._quad_recieve(self._config.word_width))
        return content


    async def _transaction(self, frame_start, frame_end):
        await frame_start
        self.idle.clear()

        self._opcode = await self._recieve_bits(8, frame_end)
        await self._sclk.value_change   # await the negative clock edge (why does )
        self._address = await self._recieve_bits(24, frame_end, self._config.is_quad_mode)
        await frame_end
