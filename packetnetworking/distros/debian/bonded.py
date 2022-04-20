from .. import NetworkBuilder
from ...utils import generate_persistent_names_udev


class DebianBondedNetwork(NetworkBuilder):
    def build(self):
        if self.network.bonding.link_aggregation not in ("bonded", "mlag_ha"):
            return

        super().build()
        self.build_tasks()

    def build_tasks(self):
        self.task_template("etc/network/interfaces", "bonded/etc_network_interfaces.j2")
        self.task_template("etc/modules", "bonded/etc_modules.j2", write_mode="a")

        os = self.metadata.operating_system

        if os.distro == "debian" and os.version not in ["7", "8"]:
            self.tasks.update(generate_persistent_names_udev())
        elif os.distro == "ubuntu" and os.version in [
            "14.04",
            "18.04",
            "19.04",
            "19.10",
            "20.04",
            "20.10",
            "21.04",
            "22.04",
        ]:
            self.tasks.update(generate_persistent_names_udev())
        return self.tasks
