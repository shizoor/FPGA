# Displays an arbitrary picture specified.   Change this line : image = Image.open('pictures/tinylion.png')   
# To do : find why there's a fault on the leftmost pixels.

from typing import List
from array import *
import numpy
import PIL
from PIL import Image


from nmigen import *
from nmigen_boards.ice40_hx1k_blink_evn import *
from nmigen.build import Platform, Resource, Pins, Clock, Attrs
from nmigen.build.run import LocalBuildProducts
from nmigen.back.pysim import Simulator, Delay
from math import ceil, log2
from nmigen_soc.memory import *
from nmigen_soc.wishbone import *

from nmigen.vendor.lattice_ice40 import LatticeICE40Platform



simulate = False

# Simulated read-only memory module.     Taken from https://vivonomicon.com/2020/04/14/learning-fpga-design-with-nmigen/
class ROM( Elaboratable, Interface ):
  def __init__( self, data ):
    # Record size.
    self.size = len( data )
    # Data storage.
    self.data = Memory( width = 16, depth = self.size, init = data )
    # Memory read port.
    self.r = self.data.read_port()
    # Initialize Wishbone bus interface.
    Interface.__init__( self,
                        data_width = 8,
                        addr_width = ceil( log2( self.size + 1 ) ) )
    self.memory_map = MemoryMap( data_width = self.data_width,
                                 addr_width = self.addr_width,
                                 alignment = 0 )
  def elaborate( self, platform ):
    m = Module()
    # Register the read port submodule.
    m.submodules.r = self.r
    # 'ack' signal should rest at 0.
    m.d.sync += self.ack.eq( 0 )
    # Simulated reads only take one cycle, but only acknowledge
    # them after 'cyc' and 'stb' are asserted.
    with m.If( self.cyc ):
      m.d.sync += self.ack.eq( self.stb )
    # Set 'dat_r' bus signal to the value in the
    # requested 'data' array index.
    m.d.comb += [
      self.r.addr.eq( self.adr ),
      self.dat_r.eq( self.r.data )
    ]
    # End of simulated memory module.
    return m





def reverse_bits(n, no_of_bits):
    result = 0
    for i in range(no_of_bits):
        result <<= 1
        result |= n & 1
        n >>= 1
    return result


class Leds(Elaboratable):
    def __init__(self):
        self.x = Signal(8)
        
    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        if(simulate == False):
            self.led0 = platform.request("led0", 0)
            self.led1 = platform.request("led1", 0)
            self.led2 = platform.request("led2", 0)
            self.led3 = platform.request("led3", 0)
            self.led4 = platform.request("led4", 0)
            self.led5 = platform.request("led5", 0)
            self.led6 = platform.request("led6", 0)
            self.led7 = platform.request("led7", 0)
        
            m.d.sync += self.led0.o.eq(self.x[0])
            m.d.sync += self.led1.o.eq(self.x[1])
            m.d.sync += self.led2.o.eq(self.x[2])
            m.d.sync += self.led3.o.eq(self.x[3])
            m.d.sync += self.led4.o.eq(self.x[4])
            m.d.sync += self.led5.o.eq(self.x[5])
            m.d.sync += self.led6.o.eq(self.x[6])
            m.d.sync += self.led7.o.eq(self.x[7])
        
        return m

    def ports(self) -> List[Signal]:
        return[self.x]


class Vgapins(Elaboratable):
    def __init__(self):
        self.x = Signal(10)
        self.h_sync = Signal(1)
        self.v_sync = Signal(1)
    
    def elaborate(self, platform: Platform) -> Module:
        m = Module()

        self.h_s = platform.request("h_sync", 0)
        self.v_s = platform.request("v_sync", 0)

        self.red0 = platform.request("red0", 0)
        self.red1 = platform.request("red1", 0)
        self.red2 = platform.request("red2", 0)

        self.green0 = platform.request("green0", 0)
        self.green1 = platform.request("green1", 0)
        self.green2 = platform.request("green2", 0)

        self.blue0 = platform.request("blue0", 0)
        self.blue1 = platform.request("blue1", 0)
        self.blue2 = platform.request("blue2", 0)
        
        self.testpin = platform.request("testpin", 0)
        m.d.comb += self.testpin.eq(1)
                
        m.d.sync += self.red0.o.eq(self.x[0])
        m.d.sync += self.red1.o.eq(self.x[1])
        m.d.sync += self.red2.o.eq(self.x[2])

        m.d.sync += self.green0.o.eq(self.x[3])
        m.d.sync += self.green1.o.eq(self.x[4])
        m.d.sync += self.green2.o.eq(self.x[5])

        m.d.sync += self.blue0.o.eq(self.x[6])
        m.d.sync += self.blue1.o.eq(self.x[7])
        m.d.sync += self.blue2.o.eq(self.x[8])
        
        m.d.sync += self.h_s.o.eq(self.h_sync)
        m.d.sync += self.v_s.o.eq(self.v_sync)

        return m

    
    def ports(self) -> List[Signal]:
        return[self.x]


class vgasignal(Elaboratable):
    horiz_freq = 31469
    clock_freq = 12000000
    horiz_cycles = int(clock_freq/horiz_freq)
    def __init__(self):
        self.h_timer =  Signal(28)
        self.v_timer =  Signal(32)
        self.v_line = Signal(unsigned(10))
        self.h_line = Signal(unsigned(10))
        self.framecounter = Signal(unsigned(256)) 
        self.memory = Signal(9)
    

    def elaborate(self, platform):
        m = Module()

        image = Image.open('pictures/burntsmileysmall.png')   #open the graphic.     
        maxsize = (267, 480)
        image.thumbnail(maxsize, PIL.Image.ANTIALIAS)
        image.show()
        imgarr = numpy.array(image)
        imagelist = []
        p = Signal(18)   #pointer for the rom containing the picture
        print(imgarr.shape)
        for i in range (imgarr.shape[0]):
            for j in range (imgarr.shape[1]):
                red = int(imgarr[i][j][0]/32)
                green = int(imgarr[i][j][1]/32)
                blue =  int(imgarr[i][j][2]/32)
                
                red = reverse_bits(red, 3)
                green = reverse_bits(green, 3)
                blue = reverse_bits(blue, 3)

                imagelist.append((red+8*green+64*blue))
        
        print("videomem programmed\n")
        v_out = Signal(9) 
        xstretchrate = Signal(17)
        xpos17 = Signal(17)
        ystretchrate = Signal(17)
        ypos17 = Signal(17)
        xpos9 = Signal(9)
        ypos9 = Signal(9)
        
        clockcounter1 = Signal(128)
        clockcounter2 = Signal(128)
        noisevalue1 = Signal(128)
        noisevalue2 = Signal(128)
        noisevalue3 = Signal(128)

        noisevalue4 = Signal(128)
        noisevalue5 = Signal(128)
        noisevalue6 = Signal(128)
        
        vhsskewtrig = Signal(3)        

        outvalue1 = Signal(9)
                                    # Logic for generating noise, meant to look like TV interference.   Be creative.
        m.d.sync+=clockcounter1.eq(clockcounter1+1)     
        m.d.sync+=clockcounter2.eq(clockcounter2-2)
        m.d.sync+=noisevalue1.eq((clockcounter1*self.framecounter)^(clockcounter2*self.h_line))
        m.d.sync+=noisevalue2.eq((clockcounter1*self.v_timer)^(clockcounter2*self.v_line))
        m.d.sync+=noisevalue3.eq(noisevalue1&noisevalue2)
        
        m.d.sync+=noisevalue4.eq(self.h_line^self.h_timer)
        m.d.sync+=noisevalue5.eq(self.v_line^self.v_timer)
        m.d.sync+=noisevalue6.eq(noisevalue5*noisevalue4)
        
        
        m.d.comb+=xstretchrate.eq(int(256*imgarr.shape[1]/maxsize[0]))
        m.d.comb+=ystretchrate.eq(int(256*imgarr.shape[0]/maxsize[1]))
        
        m.submodules.rom = rom = ROM(imagelist)
        m.submodules.leds = leds = Leds()
        m.submodules.vgapins = vgapins = Vgapins()
        
        
        with m.If(self.v_timer == 0 ):m.d.sync += self.h_timer.eq(0)
        with m.Elif(self.h_timer < 386):m.d.sync += self.h_timer.eq(self.h_timer+1)      
        with m.Else():
            m.d.sync += (self.h_timer.eq(0))
            m.d.sync += (self.v_line.eq(self.v_line+1))
        
        m.d.sync += self.v_timer.eq(self.v_timer + 1)
        
        with m.If(self.v_timer == 200000):
            m.d.sync += self.v_timer.eq(1)
            m.d.sync += self.v_line.eq(0)
            m.d.sync += self.h_line.eq(0)
            m.d.sync += self.framecounter.eq(self.framecounter+1)
            m.d.sync += vhsskewtrig.eq(noisevalue6[0:2])

        with m.If(self.h_timer >= 341):   # make the h_sync pulse, 46 cycles
            m.d.sync += vgapins.h_sync.eq(0)
        with m.Else():
            m.d.sync += vgapins.h_sync.eq(1)
        
        
        with m.If(self.v_timer >= 188000):  # make the v sync pulse
            m.d.sync += vgapins.v_sync.eq(0)
        with m.Else():
            m.d.sync += vgapins.v_sync.eq(1)
        
        
        m.d.sync += leds.x.eq(self.v_line);
        
        frontvpl = 40 #horizontal lines
        fronthpl = 26 #pixels
    
        vhsskew = Signal(9)  #For emulating tracking slip on old VHS recorders
        with m.If(vhsskewtrig>0):
            with m.If(ypos9<(20*vhsskewtrig)):
                m.d.sync+=vhsskew.eq(((20*vhsskewtrig)-ypos9)*3)
            with m.Else():
                m.d.sync+=vhsskew.eq(0)

        with m.If(self.v_line >= frontvpl):
            with m.If (self.h_timer > fronthpl):   
                    m.d.sync+=xpos17.eq(xstretchrate*((self.h_timer-fronthpl)+2))   #-fronthpl+2
                    m.d.sync+=ypos17.eq(ystretchrate*self.v_line-frontvpl)
                    m.d.sync+=xpos9.eq(xpos17[-9:-1])
                    m.d.sync+=ypos9.eq(ypos17[-9:-1])

                    m.d.sync+=p.eq(imgarr.shape[1]*ypos9+xpos9)
                    m.d.sync+=rom.adr.eq(vhsskew+p-((noisevalue6*self.framecounter)[0:3]))   #Adds horizontal synch noise
                    m.d.sync+=outvalue1.eq(rom.dat_r)
                    m.d.sync+=vgapins.x.eq(outvalue1+noisevalue3[0:9])
                    
            with m.Else():
                    m.d.sync+=vgapins.x.eq(0)


        
        with m.If(self.v_timer > 188000): m.d.sync+=vgapins.x.eq(0)
        
        with m.If(self.h_timer < 26): m.d.sync+=vgapins.x.eq(0)
        with m.If(self.h_timer > 323): m.d.sync+=vgapins.x.eq(0)

        return m
    
    
    def ports(self) -> List[Signal]:
        return[self.v_timer, self.h_timer]

    

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
    Resource("h_sync", 0, Pins("C16", dir = "o"),           #Horizontal sync for VGA output : C16  Refer to the wiring diagram attached.
        Attrs(IO_STANDARD="SB_LVCMOS")),
    Resource("v_sync", 0, Pins("B16", dir = "o"),           #Vertical sync for VGA output : B16  
        Attrs(IO_STANDARD="SB_LVCMOS")),
    Resource("red0", 0, Pins("D14", dir = "o"),             #colour0 MSB, colour2 LSB
        Attrs(IO_STANDARD="SB_LVCMOS")),
    Resource("red1", 0, Pins("E16", dir = "o"),             
        Attrs(IO_STANDARD="SB_LVCMOS")),        
    Resource("red2", 0, Pins("D15", dir = "o"),             
        Attrs(IO_STANDARD="SB_LVCMOS")),
    Resource("green0", 0, Pins("F16", dir = "o"),
        Attrs(IO_STANDARD="SB_LVCMOS")),
    Resource("green1", 0, Pins("E14", dir = "o"),
        Attrs(IO_STANDARD="SB_LVCMOS")),
    Resource("green2", 0, Pins("G16", dir = "o"),
        Attrs(IO_STANDARD="SB_LVCMOS")),
    Resource("blue0", 0, Pins("D16", dir = "o"),
        Attrs(IO_STANDARD="SB_LVCMOS")),
    Resource("blue1", 0, Pins("F15", dir = "o"),
        Attrs(IO_STANDARD="SB_LVCMOS")),
    Resource("blue2", 0, Pins("H16", dir = "o"),
        Attrs(IO_STANDARD="SB_LVCMOS")),
    Resource("testpin", 0, Pins("N16", dir = "o"),
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
    i=0
    #m = Module()

    if(simulate == False):
        Board().build(vgasignal(), do_program=False)
    else:
        m.submodules.vgasignal = vga_signal = vgasignal()
        sim = Simulator(m)
        sim.add_clock(8.3e-8)
        def process():
            for i in range (1, 40000):
                yield
        sim.add_sync_process(process)
        with sim.write_vcd("test.vcd", "test.gtkw", traces=[] + vga_signal.ports()):
            sim.run()


