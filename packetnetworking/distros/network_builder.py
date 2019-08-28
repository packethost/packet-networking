import os
import logging
from textwrap import dedent
from jinja2 import Template, StrictUndefined

log = logging.getLogger()


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

    def render(self):
        if self.tasks is None:
            self.build()
        rendered_tasks = {}
        if not self.tasks:
            return rendered_tasks
        for path, template in self.tasks.items():
            log.debug("Rendering task: '{}'".format(path))
            if template is None:
                rendered_tasks[path] = template
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
            if mode is None:
                rendered_tasks[path] = template.render(self.context())
            else:
                rendered_tasks[path] = {
                    "mode": mode,
                    "content": template.render(self.context()),
                }
        return rendered_tasks

    def run(self, rootfs_path):
        rendered_tasks = self.render()
        for relpath, content in rendered_tasks.items():
            log.debug("Processing task: '{}'".format(relpath))
            abspath = os.path.join(rootfs_path, relpath)
            if content is None:
                if os.path.exists(abspath):
                    log.info("Removing '{}'".format(abspath))
                    os.remove(abspath)
                else:
                    log.debug(
                        "Skipped removing '{}' Path doesn't exist".format(abspath)
                    )
                continue

            mode = None
            if isinstance(content, dict):
                mode = content.get("mode", None)
                content = content.get("content")

            name_dir = os.path.dirname(abspath)
            if name_dir and not os.path.exists(name_dir):
                log.debug("Making directory '{}'".format(name_dir))
                os.makedirs(name_dir, exist_ok=True)

            log.debug("Writing content to '{}'".format(abspath))
            with open(abspath, "w") as f:
                f.write(content)

            if mode:
                os.chmod(abspath, mode)
