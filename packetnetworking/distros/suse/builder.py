from .. import DistroBuilder
from .bonded import SuseBondedNetwork
from .individual import SuseIndividualNetwork


class SuseBuilder(DistroBuilder):
    distros = ["opensuseproject", "suselinux", "suse"]
    network_builders = [SuseBondedNetwork, SuseIndividualNetwork]
