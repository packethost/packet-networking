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
            for builder in self.builders:
                builder.run(rootfs_path)
            return True


def get_distro_builder(distro):
    catch_all = None
    for builder in DistroBuilder.__subclasses__():
        if isinstance(builder.distros, list) and distro in builder.distros:
            return builder
        elif builder.distros == "*":
            catch_all = builder
    return catch_all
