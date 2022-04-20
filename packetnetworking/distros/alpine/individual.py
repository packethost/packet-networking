from .. import NetworkBuilder
from ...utils import generate_persistent_names_mdev


class AlpineIndividualNetwork(NetworkBuilder):
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

        self.tasks.update(generate_persistent_names_mdev())

        return self.tasks
