"""
Simulation model for S25HS256T / S25HS512T / S25HS01GT / S25HL256T / S25HL512T / S25HL01GT
"""

from collections import deque

from cocotb.triggers import FallingEdge
from cocotb.triggers import First
from cocotb.triggers import RisingEdge

from ...exceptions import QSpiFrameError
from ...spi import QSpiBus
from ...spi import QSpiConfig
from ...spi import QSpiSubordinateBase


class S25HS256T(QSpiSubordinateBase):
    _config = SpiConfig(
        word_width=8,
        cpol=True,
        cpha=False,
        msb_first=True,
        frame_spacing_ns=6,
        cs_active_low=True,
        is_quad_mode=False,
    )


    async def _recieve_bits(self, num_bits, quad_mode=False):
        if not quad_mode:
            tx_word = self._out_queue.popleft()
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

        opcode = _recieve_bits(8)
        address = _recieve_bits(24, self._config.is_quad_mode)
        print(f"opcode {opcode}\naddress {address}")
        await frame_end
