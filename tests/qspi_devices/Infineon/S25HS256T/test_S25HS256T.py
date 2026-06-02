# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2023 Spencer Chang
import logging
import os

import cocotb
import cocotb_test.simulator
from cocotb.triggers import Timer

from cocotbext.qspi import QSpiBus
from cocotbext.qspi import QSpiConfig
from cocotbext.qspi import QSpiManager
from cocotbext.qspi.devices.Infineon.S25HS256T import S25HS256T


class TB:
    def __init__(self, dut):
        self.dut = dut
        self.log = logging.getLogger("cocotb.tb")
        self.log.setLevel(logging.DEBUG)

        self.bus = QSpiBus.from_entity(dut, cs_name="ncs")

        self.config = QSpiConfig(
            word_width=8,
            cpol=False,
            cpha=False,
            msb_first=True,
            frame_spacing_ns=6,
            cs_active_low=True,
            is_quad_mode=False,
        )

        self.source = QSpiManager(self.bus, self.config)
        self.sink = S25HS256T(self.bus)


def convert_int_to_bytes(input, num_bytes):
    # Source - https://stackoverflow.com/a/32490254
    # Posted by jojonas
    numbers = list((input >> i) & 0xFF for i in range(0, num_bytes*8, 8))
    return list(reversed(numbers))


@cocotb.test()
async def run_test_S25HS256T(dut):
    tb = TB(dut)
    await Timer(10, 'us')

    await tb.source.write(convert_int_to_bytes(0x03000042, 4), burst=True)
    await tb.sink.idle.wait()
    assert tb.sink._opcode  == 0x3
    assert tb.sink._address == 0x42

tests_dir = os.path.dirname(__file__)

def test_S25HS256T(request):
    dut = "test_S25HS256T"
    module = os.path.splitext(os.path.basename(__file__))[0]
    toplevel = dut
    sources = [
        os.path.join(tests_dir, f"{dut}.v"),
    ]

    parameters = {}
    extra_env = {f'PARAM_{k}': str(v) for k, v in parameters.items()}

    sim_build = os.path.join(
        tests_dir, "sim_build",
        request.node.name.replace('[', '-').replace(']', ''),
    )

    cocotb_test.simulator.run(
        python_search=[tests_dir],
        verilog_sources=sources,
        toplevel=toplevel,
        module=module,
        parameters=parameters,
        sim_build=sim_build,
        extra_env=extra_env,
    )