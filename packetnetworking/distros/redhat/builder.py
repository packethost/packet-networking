from .. import DistroBuilder
from .bonded import RedhatBondedNetwork
from .individual import RedhatIndividualNetwork


class RedhatBuilder(DistroBuilder):
    distros = [
        "almalinux",
        "centos",
        "redhatenterprise",
        "redhatenterpriseserver",
        "rocky",
    ]
    network_builders = [RedhatBondedNetwork, RedhatIndividualNetwork]

    def build_tasks(self):
        self.task_template("etc/hostname", "etc_hostname.j2")
        self.task_template("etc/resolv.conf", "etc_resolv.conf.j2")
        self.task_template("etc/hosts", "etc_hosts.j2")
