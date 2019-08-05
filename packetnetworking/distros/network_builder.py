import os
from textwrap import dedent
from jinja2 import Template, StrictUndefined


class NetworkBuilder:
    def __init__(self, metadata):
        self.metadata = metadata
        self.network = self.metadata.network
        self.tasks = None

    @property
    def ipv4pub(self):
        return self.network.addresses.management.public.ipv4

    @property
    def ipv6pub(self):
        return self.network.addresses.management.public.ipv6

    @property
    def ipv4priv(self):
        return self.network.addresses.management.private.ipv4

    def context(self):
        return {
            "hostname": self.metadata.hostname,
            "interfaces": self.network.interfaces,
            "ip4priv": self.ipv4priv.first,
            "ip4pub": self.ipv4pub.first,
            "ip6pub": self.ipv6pub.first,
            "net": self.network,
            "osinfo": self.metadata.operating_system,
            "resolvers": self.network.resolvers,
        }

    def run(self, rootfs_path):
        if self.tasks is None:
            self.build()
        for name, template in self.tasks.items():
            print("Processing task: '{}'".format(name))
            name = os.path.join(rootfs_path, name)
            if template is None:
                if os.path.exists(name):
                    os.remove(name)
                continue

            mode = None
            if isinstance(template, dict):
                mode = template.get("mode", None)
                template = template.get("template")

            template = Template(
                dedent(template),
                keep_trailing_newline=True,
                lstrip_blocks=True,
                trim_blocks=True,
                undefined=StrictUndefined,
            )

            name_dir = os.path.dirname(name)
            if name_dir and not os.path.exists(name_dir):
                os.makedirs(name_dir, exist_ok=True)

            with open(name, "w") as f:
                f.write(template.render(self.context()))

            if mode:
                os.chmod(name, mode)
