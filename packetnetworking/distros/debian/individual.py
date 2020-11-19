from .. import NetworkBuilder
from ...utils import generate_persistent_names


# pylama:ignore=E501
class DebianIndividualNetwork(NetworkBuilder):
    def build(self):
        if self.network.bonding.link_aggregation == "individual":
            self.build_tasks()

    def build_tasks(self):
        self.tasks = {}

        self.task_template(
            "etc/network/interfaces", "individual/etc_network_interfaces.j2"
        )

        os = self.metadata.operating_system

        if os.distro == "debian" and os.version in ["10", "11"]:
            self.tasks.update(generate_persistent_names())
        elif os.distro == "ubuntu" and os.version in [
            "14.04",
            "19.04",
            "19.10",
            "20.04",
            "20.10",
            "21.04",
        ]:
            self.tasks.update(generate_persistent_names())
        return self.tasks
