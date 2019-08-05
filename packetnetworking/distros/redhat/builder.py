from .. import DistroBuilder
from .bonded import RedhatBondedNetwork


class RedhatBuilder(DistroBuilder):
    distros = ["centos", "redhatenterpriseserver", "scientificcernslc"]
    network_builders = [RedhatBondedNetwork]
