from .. import DistroBuilder
from .bonded import RedhatBondedNetwork
from .individual import RedhatIndividualNetwork


class RedhatBuilder(DistroBuilder):
    distros = [
        "centos",
        "redhatenterpriseserver",
        "redhatenterprise",
        "scientificcernslc",
    ]
    network_builders = [RedhatBondedNetwork, RedhatIndividualNetwork]
