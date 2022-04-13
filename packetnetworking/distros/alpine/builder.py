from .. import DistroBuilder
from .bonded import AlpineBondedNetwork
from .individual import AlpineIndividualNetwork


class AlpineBuilder(DistroBuilder):
    distros = ["alpine"]
    network_builders = [AlpineBondedNetwork, AlpineIndividualNetwork]

    def build_tasks(self):
        self.task_template("etc/hostname", "etc_hostname.j2")
        self.task_template("etc/resolv.conf", "etc_resolv.conf.j2")
        self.task_template("etc/hosts", "etc_hosts.j2")
