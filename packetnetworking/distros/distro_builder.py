class DistroBuilder:
    distros = None
    network_builders = []

    def __init__(self, metadata):
        self.metadata = metadata
        self.builders = []

    def build(self):
        for NetworkBuilder in self.network_builders:
            builder = NetworkBuilder(self.metadata)
            self.builders.append(builder)
            builder.build()
        return True

    def run(self, rootfs_path):
        if self.builders:
            tasks_found = False
            for builder in self.builders:
                if builder.run(rootfs_path):
                    tasks_found = True
            if not tasks_found:
                return None
            return True


def get_distro_builder(distro):
    catch_all = None
    for builder in DistroBuilder.__subclasses__():
        if isinstance(builder.distros, list) and distro.lower() in builder.distros:
            return builder
        elif builder.distros == "*":
            catch_all = builder
    return catch_all
