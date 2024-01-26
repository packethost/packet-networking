from .. import NetworkBuilder
from ...utils import generate_persistent_names_udev
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

        for bond in self.network.bonds:
            self.task_template(
                "etc/sysconfig/network-scripts/ifcfg-{}".format(bond),
                "bonded/etc_sysconfig_network-scripts_ifcfg-bondX.j2",
                context={"bond": bond},
            )

            if self.ipv4pub and bond == "bond0":
                # Only needed when a public ip is used, otherwise private ip is
                # already set and no special routes are needed.
                self.task_template(
                    "etc/sysconfig/network-scripts/ifcfg-{}:0".format(bond),
                    "bonded/etc_sysconfig_network-scripts_ifcfg-bondX_0.j2",
                    context={"bond": bond},
                )
                self.task_template(
                    "etc/sysconfig/network-scripts/route-{}".format(bond),
                    "bonded/etc_sysconfig_network-scripts_route-bondX.j2",
                    context={"bond": bond},
                )

        for i, iface in enumerate(self.network.interfaces):
            name = iface["name"]
            self.task_template(
                "etc/sysconfig/network-scripts/ifcfg-" + name,
                "bonded/etc_sysconfig_network-scripts_ifcfg-template.j2",
                context={"iface": name, "i": i},
            )
            self.task_template(
                "etc/systemd/network/70-" + name + ".link",
                "bonded/etc_systemd_network-70-template.j2",
                context={"iface": name, "i": i},
            )

        self.task_template(
            "sbin/ifup-pre-local", "bonded/sbin_ifup-pre-local.j2", mode=0o755
        )

        if self.metadata.operating_system.distro not in (
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
            self.tasks.update(generate_persistent_names_udev())
        return self.tasks
