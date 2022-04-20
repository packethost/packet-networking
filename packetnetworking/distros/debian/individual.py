from .. import NetworkBuilder
from ...utils import generate_persistent_names_udev


class DebianIndividualNetwork(NetworkBuilder):
    def build(self):
        if self.network.bonding.link_aggregation != "individual":
            return

        super().build()
        self.build_tasks()

    def build_tasks(self):
        template = "individual/etc_network_interfaces.j2"
        if self.dhcp:
            template = "dhcp/etc_network_interfaces.j2"

        self.task_template("etc/network/interfaces", template)

        os = self.metadata.operating_system

        if os.distro == "debian" and os.version in ["10", "11"]:
            self.tasks.update(generate_persistent_names_udev())
        elif os.distro == "ubuntu" and os.version in [
            "14.04",
            "18.04",
            "19.04",
            "19.10",
            "20.04",
            "20.10",
            "21.04",
        ]:
            self.tasks.update(generate_persistent_names_udev())
        return self.tasks
