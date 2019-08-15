from .builder_hook import BuilderHook


class SingleInterfaceHook(BuilderHook):
    plans = ["baremetal_1e", "x1.small.x86"]

    def hook_initialized(self, builder):
        if builder.metadata.plan.lower() in self.plans:
            builder.network.interfaces = builder.network.interfaces[:1]
