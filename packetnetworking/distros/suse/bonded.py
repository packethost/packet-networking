from .. import NetworkBuilder


class SuseBondedNetwork(NetworkBuilder):
    def build(self):
        if self.network.bonding.link_aggregation not in ("bonded", "mlag_ha"):
            return

        super().build()
        self.build_tasks()

    def build_tasks(self):
        self.task_template(
            "etc/modprobe.d/bonding.conf", "bonded/etc_modprobe.d_bonding.conf.j2"
        )
        self.task_template(
            "etc/sysconfig/network/ifcfg-bond0",
            "bonded/etc_sysconfig_network_ifcfg-bond0.j2",
        )
        self.task_template(
            "etc/sysconfig/network/routes", "bonded/etc_sysconfig_network_routes.j2"
        )

        for i in range(len(self.network.interfaces)):
            name = self.network.interfaces[i]["name"]
            self.task_template(
                "etc/sysconfig/network/ifcfg-" + name,
                "bonded/etc_sysconfig_network_ifcfg-template.j2",
                fmt={"iface": name, "i": i},
            )

        return self.tasks
