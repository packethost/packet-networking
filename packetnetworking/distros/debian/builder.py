from .. import DistroBuilder
from .bonded import DebianBondedNetwork
from .individual import DebianIndividualNetwork


class DebianBuilder(DistroBuilder):
    distros = ["debian", "ubuntu"]
    network_builders = [DebianBondedNetwork, DebianIndividualNetwork]

    def build_tasks(self):
        self.task_template("etc/hostname", "etc_hostname.j2")
        self.task_template("etc/hosts", "etc_hosts.j2")
        if self.metadata.operating_system.distro == "ubuntu":
            # this should probably be a check if etc/resolv.conf symlinks to ../run/systemd/resolve/stub-resolv.conf instead
            self.task_template(
                "etc/systemd/resolved.conf", "etc_systemd_resolved.conf.j2"
            )
        else:
            self.task_template("etc/resolv.conf", "etc_resolv.conf.j2")
