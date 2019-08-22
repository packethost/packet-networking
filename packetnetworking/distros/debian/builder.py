from .. import DistroBuilder
from .bonded import DebianBondedNetwork
from .individual import DebianIndividualNetwork


class DebianBuilder(DistroBuilder):
    distros = ["debian", "ubuntu"]
    network_builders = [DebianBondedNetwork, DebianIndividualNetwork]
