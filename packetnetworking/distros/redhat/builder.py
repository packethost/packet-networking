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

    def build_tasks(self):
        self.tasks = {}

        self.task_template("etc/hostname", "etc_hostname.j2")
        self.task_template("etc/resolv.conf", "etc_resolv.conf.j2")
        self.task_template("etc/hosts", "etc_hosts.j2")

        return self.tasks
