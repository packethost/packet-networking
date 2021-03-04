from .. import NetworkBuilder
from ...utils import generate_persistent_names
import os


class RedhatBondedNetwork(NetworkBuilder):
    def build(self):
        if self.network.bonding.link_aggregation not in ("bonded", "mlag_ha"):
            return

        super().build()
        self.build_tasks()

    def build_tasks(self):
        self.task_template("etc/sysconfig/network", "bonded/etc_sysconfig_network.j2")
        self.task_template(
            "etc/modprobe.d/bonding.conf", "bonded/etc_modprobe.d_bonding.conf.j2"
        )
        self.task_template(
            "etc/sysconfig/network-scripts/ifcfg-bond0",
            "bonded/etc_sysconfig_network-scripts_ifcfg-bond0.j2",
        )

        if self.ipv4pub:
            # Only needed when a public ip is used, otherwise private ip is
            # already set and no special routes are needed.
            self.task_template(
                "etc/sysconfig/network-scripts/ifcfg-bond0:0",
                "bonded/etc_sysconfig_network-scripts_ifcfg-bond0_0.j2",
            )
            self.task_template(
                "etc/sysconfig/network-scripts/route-bond0",
                "bonded/etc_sysconfig_network-scripts_route-bond0.j2",
            )

        for i, iface in enumerate(self.network.interfaces):
            name = iface["name"]
            self.task_template(
                "etc/sysconfig/network-scripts/ifcfg-" + name,
                "bonded/etc_sysconfig_network-scripts_ifcfg-template.j2",
                fmt={"iface": name, "i": i},
            )

        self.task_template(
            "sbin/ifup-pre-local", "bonded/sbin_ifup-pre-local.j2", mode=0o755
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
