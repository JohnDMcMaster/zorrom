from zorrom import mcs48
from zorrom import mb8623x
#from zorrom import snes

arch2mr = {
    'd8041ah': mcs48.D8041AH,
    'mb8623x': mb8623x.MB8623x,
    'm5l8042': mcs48.M5L8042,
    #'snes_cic': snes.SnesCIC,
    #'snes_pif': snes.SnesPIF,
}


def get_arch(arch):
    try:
        return arch2mr[arch]()
    except KeyError:
        raise Exception("Invalid architecture %s. Try --list-arch" % arch)
