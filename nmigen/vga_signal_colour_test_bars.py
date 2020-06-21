# VGA colour test bars.   Add colourbars.png or a file of your choosing into a 
# directory called pictures.  10 px high, 266 px wide.  

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


from nmigen.vendor.lattice_ice40 import LatticeICE40Platform


#Lookup table for the alphabet

simulate = False


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
        self.framecounter = Signal(unsigned(24)) 
        self.memory = Signal(9)
    

    def elaborate(self, platform):
        m = Module()

        #videomem  = Array([Signal(unsigned(9)) for _ in range(330)])  # 330 pixels per line 480 lines 266 usable
        videomem = Array([Array([Signal(unsigned(9)) for _ in range(330)]) for _ in range(481)])  #This is bad.  Use memory, and make it smaller than 128k
        image = Image.open('pictures/colourbars.png')   #open the graphic.   Use 10 pixels vertically.  
        maxsize = (267,480)
        image.thumbnail(maxsize, PIL.Image.ANTIALIAS)
        image.show()
        imgarr = numpy.array(image)
        print(imgarr.shape)
        for i in range (imgarr.shape[0]):
            for j in range (imgarr.shape[1]):
                red = int(imgarr[i][j][0]/32)
                green = int(imgarr[i][j][1]/32)
                blue =  int(imgarr[i][j][2]/32)
                
                red = reverse_bits(red, 3)
                green = reverse_bits(green, 3)
                blue = reverse_bits(blue, 3)

                m.d.sync+=videomem[j][i].eq(red+8*green+64*blue)
        
        print("videomem programmed\n")
        v_out = Signal(9) 
        
        


        m.submodules.leds = leds = Leds()
        m.submodules.vgapins = vgapins = Vgapins()
        
        
        #m.d.sync += self.h_timer.eq(self.v_timer%386)  # This doesn't work
        with m.If(self.v_timer == 0 ):m.d.sync += self.h_timer.eq(0)
        with m.Elif(self.h_timer < 386):m.d.sync += self.h_timer.eq(self.h_timer+1)     #this does  
        with m.Else():
            m.d.sync += (self.h_timer.eq(0))
            m.d.sync += (self.v_line.eq(self.v_line+1))
        
        m.d.sync += self.v_timer.eq(self.v_timer + 1)
        
        with m.If(self.v_timer == 200000):
            m.d.sync += self.v_timer.eq(1)
            m.d.sync += self.v_line.eq(0)
            m.d.sync += self.h_line.eq(0)
            m.d.sync += self.framecounter.eq(self.framecounter+1)

        with m.If(self.h_timer >= 341):   # make the h_sync pulse, 46 cycles
            m.d.sync += vgapins.h_sync.eq(0)
        with m.Else():
            m.d.sync += vgapins.h_sync.eq(1)
        
        
        with m.If(self.v_timer >= 188000):
            m.d.sync += vgapins.v_sync.eq(0)
        with m.Else():
            m.d.sync += vgapins.v_sync.eq(1)
        
        
        #with m.If(self.v_timer <= 188000):
        #    with m.If (self.h_timer > 56):
        #        with m.If (self.h_timer < 323):             #Allow for back porch and front
        #            #m.d.sync+=vgapins.x.eq(videomem[0][0])                        #Display a test line
        #            m.d.sync+=self.h_line.eq(self.h_line+1)
        #            m.d.sync+=v_out.eq(v_out+1)
        m.d.sync += leds.x.eq(self.v_line);
        for i in range (0, 10):      #The first line flickers, possibly start from line 1
            with m.If (self.v_line <= int((i+1)*48)):       #the multiply by 48 is to scale the image vertically, remove for correct aspect ratio
                with m.If(self.v_line >= int(i)*48):
                    with m.If (self.h_timer > 56):
                        with m.If (self.h_timer < 323):   #make this 323 again after
                            m.d.sync+=vgapins.x.eq(videomem[self.h_timer-57][i])
                        with m.Else():
                            m.d.sync+=vgapins.x.eq(0)


        
        with m.If(self.v_timer > 188000): m.d.sync+=vgapins.x.eq(0)
        
        with m.If(self.h_timer < 56): m.d.sync+=vgapins.x.eq(0)
        with m.If(self.h_timer > 323): m.d.sync+=vgapins.x.eq(0)

        #m.d.comb += leds.x.eq(v_sync)
        return m
    
#    def setallblack(self):
#        m = Module()
#        m.d.comb += m.red0.o.eq(0)      
#        m.d.comb += m.red1.o.eq(0)
#        m.d.comb += m.red2.o.eq(1)
#
#        m.d.comb += m.green0.o.eq(0)
#        m.d.comb += m.green1.o.eq(0)
#        m.d.comb += m.green2.o.eq(1)
#        
#        m.d.comb += m.blue0.o.eq(0)
#        m.d.comb += m.blue1.o.eq(0)
#        m.d.comb += m.blue2.o.eq(1)

    
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
    m = Module()

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


