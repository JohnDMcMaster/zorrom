from zorrom import mcs48
from zorrom import mb8623x
#from zorrom import snes
from zorrom import pic1670
from zorrom import lc5800
from zorrom import tutorial
from zorrom import lr35902
from zorrom import tms320

arch2mr = {
    'd8041ah': mcs48.D8041AH,
    'mb8623x': mb8623x.MB8623x,
    'm5l8042': mcs48.M5L8042,
    'pic1670': pic1670.PIC1670,
    #'snes_cic': snes.SnesCIC,
    #'snes_pif': snes.SnesPIF,
    'lc5800': lc5800.LC5800,
    'tutorial1': tutorial.Tutorial1,
    'lr35902': lr35902.LR35902,
    'tms32010': tms320.TMS32010,
    'tms320c15': tms320.TMS320C15,
    # 'tms320c52': tms320.TMS320C52,
    'tms320c53': tms320.TMS320C53,
}


def get_arch(arch):
    try:
        return arch2mr[arch]()
    except KeyError:
        raise Exception("Invalid architecture %s. Try --list-arch" % arch)
