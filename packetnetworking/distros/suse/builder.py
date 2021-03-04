from .. import DistroBuilder
from .bonded import SuseBondedNetwork
from .individual import SuseIndividualNetwork


class SuseBuilder(DistroBuilder):
    distros = ["opensuseproject", "suselinux", "suse"]
    network_builders = [SuseBondedNetwork, SuseIndividualNetwork]

    def build_tasks(self):
        self.task_template("etc/hostname", "etc_hostname.j2")
        self.task_template("etc/resolv.conf", "etc_resolv.conf.j2")
        self.task_template("etc/hosts", "etc_hosts.j2")
