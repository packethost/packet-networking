from .. import NetworkBuilder
from ...utils import generate_persistent_names_mdev


class AlpineBondedNetwork(NetworkBuilder):
    def build(self):
        if self.network.bonding.link_aggregation not in ("bonded", "mlag_ha"):
            return

        super().build()
        self.build_tasks()

    def build_tasks(self):
        self.task_template("etc/network/interfaces", "bonded/etc_network_interfaces.j2")
        self.task_template("etc/modules", "bonded/etc_modules.j2", write_mode="a")

        self.tasks.update(generate_persistent_names_mdev())

        return self.tasks
