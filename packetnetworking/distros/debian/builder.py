from .. import DistroBuilder
from .bonded import DebianBondedNetwork


class DebianBuilder(DistroBuilder):
    distros = ["debian", "ubuntu"]
    network_builders = [DebianBondedNetwork]
