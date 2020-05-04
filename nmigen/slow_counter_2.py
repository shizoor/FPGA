# I wanted to make a small program that has the LEDs do something rather than just blink, so I 
# made this basic "hello world" which makes them count slowly enough for the eye to register it.
# Many thanks to whitequark and Robert Baruch for their excellent resources on this.
from typing import List
from nmigen import *
from nmigen_boards.ice40_hx1k_blink_evn import *
from nmigen.build import Platform, Resource, Pins, Clock, Attrs
from nmigen.build.run import LocalBuildProducts

from nmigen.vendor.lattice_ice40 import LatticeICE40Platform

class Leds(Elaboratable):
    def __init__(self):
        self.x = Signal(8)

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        self.led0 = platform.request("led0", 0)
        self.led1 = platform.request("led1", 0)
        self.led2 = platform.request("led2", 0)
        self.led3 = platform.request("led3", 0)
        self.led4 = platform.request("led4", 0)
        self.led5 = platform.request("led5", 0)
        self.led6 = platform.request("led6", 0)
        self.led7 = platform.request("led7", 0)

        m.d.comb += self.led0.o.eq(self.x[0])
        m.d.comb += self.led1.o.eq(self.x[1])
        m.d.comb += self.led2.o.eq(self.x[2])
        m.d.comb += self.led3.o.eq(self.x[3])
        m.d.comb += self.led4.o.eq(self.x[4])
        m.d.comb += self.led5.o.eq(self.x[5])
        m.d.comb += self.led6.o.eq(self.x[6])
        m.d.comb += self.led7.o.eq(self.x[7])

        return m

    def ports(self) -> List[Signal]:
        return[self.x]


class Counter(Elaboratable):
    def elaborate(self, platform):
        m = Module()
        timer = Signal(28)
        m.submodules.leds = leds = Leds()
        
        m.d.sync += timer.eq(timer + 1)
        
        m.d.comb += leds.x.eq(timer[-9:-1])
        return m

       

class Board(LatticeICE40Platform):
    device = "iCE40HX8K"
    package = "CT256"
    resources = [
    Resource("clk1", 0, Pins("J3", dir="i"), Clock(12e6),
        Attrs(GLOBAL=True, IO_STANDARD="SB_LVCMOS")),        # GBIN6
    Resource("rst", 0, Pins("R9", dir="i"),
        Attrs(GLOBAL=True, IO_STANDARD="SB_LVCMOS")),        # GBIN5
    Resource("led0", 0, Pins("C3", dir="o"),
        Attrs(IO_STANDARD="SB_LVCMOS")),                     # LED 2
    Resource("led1", 0, Pins("B3", dir="o"),
        Attrs(IO_STANDARD="SB_LVCMOS")),                     # LED 3   Note LED pins : pins="C3 B3 C4 C5 A1 A2 B4 B5"
    Resource("led2", 0, Pins("C4", dir="o"),
        Attrs(IO_STANDARD="SB_LVCMOS")),                     # LED 4
    Resource("led3", 0, Pins("C5", dir="o"),
        Attrs(IO_STANDARD="SB_LVCMOS")),
    Resource("led4", 0, Pins("A1", dir="o"),
        Attrs(IO_STANDARD="SB_LVCMOS")),
    Resource("led5", 0, Pins("A2", dir="o"),
        Attrs(IO_STANDARD="SB_LVCMOS")),
    Resource("led6", 0, Pins("B4", dir="o"),
        Attrs(IO_STANDARD="SB_LVCMOS")),
    Resource("led7", 0, Pins("B5", dir="o"),
        Attrs(IO_STANDARD="SB_LVCMOS")),

    ]

    default_clk = "clk1"
    default_rst = "rst"
    connectors = []

    def toolchain_program(self, products: LocalBuildProducts, name: str):
        iceprog = os.environ.get("ICEPROG", "iceprog")
        with products.extract("{}.bin".format(name)) as bitstream_filename:
            subprocess.check_all([iceprog, "-S", bitstream_filename])


if __name__ == "__main__":
    
    Board().build(Counter(), do_program=False)

