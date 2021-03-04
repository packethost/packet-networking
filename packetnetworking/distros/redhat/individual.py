from .. import NetworkBuilder
from ...utils import generate_persistent_names
import os


class RedhatIndividualNetwork(NetworkBuilder):
    def build(self):
        if self.network.bonding.link_aggregation != "individual":
            return

        super().build()
        self.build_tasks()

    def build_tasks(self):
        iface0 = self.network.interfaces[0]

        self.task_template(
            "etc/sysconfig/network", "individual/etc_sysconfig_network.j2"
        )
        self.task_template(
            "etc/sysconfig/network-scripts/ifcfg-{iface0.name}".format(iface0=iface0),
            "individual/etc_sysconfig_network-scripts_ifcfg-iface0.j2",
        )

        if self.ipv4pub:
            # Only needed when a public ip is used, otherwise private ip is
            # already set and no special routes are needed.
            self.task_template(
                "etc/sysconfig/network-scripts/ifcfg-{iface0.name}:0".format(
                    iface0=iface0
                ),
                "individual/etc_sysconfig_network-scripts_ifcfg-iface0_0.j2",
            )
            self.task_template(
                "etc/sysconfig/network-scripts/route-{iface0.name}".format(
                    iface0=iface0
                ),
                "individual/etc_sysconfig_network-scripts_route-iface0.j2",
            )

        if self.metadata.operating_system.distro not in (
            "scientificcernslc",
            "redhatenterpriseserver",
            "redhatenterprise",
        ):
            for service in (
                "dbus-org.freedesktop.NetworkManager",
                "dbus-org.freedesktop.nm-dispatcher",
                "multi-user.target.wants/NetworkManager",
            ):
                self.tasks[
                    os.path.join("etc/systemd/system", service + ".service")
                ] = None
        else:
            self.tasks.update(generate_persistent_names())
        return self.tasks
