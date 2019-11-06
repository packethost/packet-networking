from .. import NetworkBuilder


# pylama:ignore=E501
class SuseIndividualNetwork(NetworkBuilder):
    def build(self):
        if self.network.bonding.link_aggregation == "individual":
            self.build_tasks()

    def build_tasks(self):
        self.tasks = {}

        iface0 = self.network.interfaces[0]

        self.task_template(
            "etc/sysconfig/network/ifcfg-" + iface0.name,
            "individual/etc_sysconfig_network_ifcfg-iface0.j2",
        )
        self.task_template(
            "etc/sysconfig/network/routes", "individual/etc_sysconfig_network_routes.j2"
        )

        for i, iface in enumerate(self.network.interfaces):
            if iface == iface0:
                # skip interface since it is already configured above
                continue
            self.task_template(
                "etc/sysconfig/network/ifcfg-" + iface.name,
                "individual/etc_sysconfig_network_ifcfg-template.j2",
                fmt={"iface": iface.name, "i": i},
            )

        return self.tasks
