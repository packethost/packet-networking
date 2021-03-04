from .. import DistroBuilder
from .bonded import DebianBondedNetwork
from .individual import DebianIndividualNetwork


class DebianBuilder(DistroBuilder):
    distros = ["debian", "ubuntu"]
    network_builders = [DebianBondedNetwork, DebianIndividualNetwork]

    def build_tasks(self):
        self.task_template("etc/hostname", "etc_hostname.j2")
        self.task_template("etc/resolv.conf", "etc_resolv.conf.j2")
        self.task_template("etc/hosts", "etc_hosts.j2")
