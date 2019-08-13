from .. import DistroBuilder
from .bonded import SuseBondedNetwork


class SuseBuilder(DistroBuilder):
    distros = ["opensuseproject", "suselinux", "suse"]
    network_builders = [SuseBondedNetwork]
