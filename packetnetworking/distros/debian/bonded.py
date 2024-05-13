from .. import NetworkBuilder
from ...utils import generate_persistent_names_udev


class DebianBondedNetwork(NetworkBuilder):
    def build(self):
        if self.network.bonding.link_aggregation not in ("bonded", "mlag_ha"):
            return

        super().build()
        self.build_tasks()

    def build_tasks(self):
        if (
            self.metadata.operating_system.distro == "debian"
            and self.metadata.operating_system.version == "10"
        ):
            # Debian10 is failing if we don't configure the net this way
            self.task_template(
                "etc/network/interfaces", "bonded/etc_network_interfaces_debian10.j2"
            )
        else:
            self.task_template(
                "etc/network/interfaces", "bonded/etc_network_interfaces.j2"
            )

        self.task_template("etc/modules", "bonded/etc_modules.j2", write_mode="a")
        self.tasks.update(generate_persistent_names_udev())
        return self.tasks
