from .builder_hook import BuilderHook


class LogicalInterfaceNamesHook(BuilderHook):
    plans = ["baremetal_hua"]

    def hook_initialized(self, builder):
        if builder.metadata.plan.lower() in self.plans:
            for iface in builder.network.interfaces:
                iface["name"] = iface["names"]["LOGICAL"]
