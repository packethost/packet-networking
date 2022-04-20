import json
import os
import re
import subprocess
import sys
from textwrap import dedent

import click

MAX_RESOLVE_DEPTH = 10
package_dir = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))


class DictAttributes(dict):
    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(
                "'{}' has no attribute '{}'".format(self.__class__.__name__, attr)
            )


def RecursiveAttributes(item):
    if isinstance(item, list):
        return RecursiveListAttributes(item)
    elif isinstance(item, dict):
        return RecursiveDictAttributes(item)
    return item


class RecursiveDictAttributes(DictAttributes):
    def __init__(self, item):
        super().__init__(item)
        for k, v in item.items():
            self[k] = RecursiveAttributes(v)

    def __setitem__(self, key, value):
        super().__setitem__(key, RecursiveAttributes(value))

    def __setattr__(self, attr, value):
        super().__setattr__(attr, RecursiveAttributes(value))


class WhereList(list):
    def __init__(self, *items, always_lower=False):
        super().__init__(*items)
        self._always_lower = always_lower

    # pylama:ignore=C901
    def where(self, cmp_lower=None, skip_missing=True, missing_default=None, **wheres):
        if cmp_lower is None:
            cmp_lower = self._always_lower
        results = WhereList()
        for item in self:
            include = True
            for k, v in wheres.items():
                try:
                    item_value = item[k]
                except KeyError:
                    if skip_missing:
                        include = False
                        break
                    else:
                        item_value = missing_default

                if cmp_lower:
                    try:
                        item_value = item_value.lower()
                    except AttributeError:
                        pass
                    try:
                        v = v.lower()
                    except AttributeError:
                        pass

                if item_value != v:
                    include = False
                    break
            if include:
                results.append(item)
        return results

    def find(self, *args, **kwargs):
        results = self.where(*args, **kwargs)
        if results:
            return results[0]


class RecursiveListAttributes(WhereList):
    def __init__(self, items):
        super().__init__(items)
        for j in range(len(items)):
            self[j] = RecursiveAttributes(self[j])

    def __setitem__(self, key, value):
        super().__setitem__(key, RecursiveAttributes(value))


class IPAddressList(WhereList):
    @property
    def first(self):
        return self[0] if self else None

    @property
    def enabled(self):
        return self.where(enabled=True)

    @property
    def disabled(self):
        return self.where(enabled=False, skip_missing=False, missing_default=False)

    @property
    def ipv4(self):
        return self.where(address_family=4)

    @property
    def ipv6(self):
        return self.where(address_family=6)

    @property
    def public(self):
        return self.where(public=True)

    @property
    def private(self):
        return self.where(public=False, skip_missing=False, missing_default=False)

    @property
    def management(self):
        return self.where(management=True)

    @property
    def not_management(self):
        return self.where(management=False, skip_missing=False, missing_default=False)

    def where(self, *args, **kwargs):
        return IPAddressList(super().where(*args, **kwargs))


class Tasks(object):
    def task(self, task, content, write_mode=None, mode=None, fmt=None):
        self.tasks[task] = {
            "file_mode": write_mode,
            "mode": mode,
            "template": content,
            "fmt": fmt,
        }
        return self.tasks[task]

    def task_template(self, task, path, write_mode=None, mode=None, fmt=None):
        path = os.path.join(package_dir, self.templates_base, path)
        t = self.task(task, None, write_mode, mode, fmt)
        t["template_path"] = path
        return t


def jfind(j, fn):
    result = []
    for i in j:
        if fn(i):
            result.append(i)

    if len(result) == 1:
        return result[0]
    else:
        return result


# resolve_path follows symlinks, making sure the path stays within the
# rootfs path provided
def resolve_path(rootfs, path, _depth=0):
    if _depth > MAX_RESOLVE_DEPTH:
        raise RecursionError("Symlink max depth reached")
    if path.startswith(rootfs):
        i = len(rootfs)
        relpath = os.path.join("/", path[i:])
        abspath = path
    else:
        relpath = os.path.join("/", path)
        abspath = os.path.normpath(os.path.join(rootfs, "." + relpath))
    if not os.path.islink(abspath):
        return abspath
    rellink = os.readlink(abspath)
    reldir = os.path.relpath(os.path.dirname(abspath), rootfs)
    sysdir = os.path.join("/", reldir)
    syslink = os.path.normpath(os.path.join(sysdir, rellink))
    return resolve_path(rootfs, syslink, _depth=_depth + 1)


def generated_header(prefix="#"):
    if prefix:
        prefix = prefix + " "

    return dedent(
        """
            {prefix}This file was automatically generated by the Equinix Metal installation environment.
            {prefix}See https://github.com/packethost/packet-networking for details.
        """.format(
            prefix=prefix
        )
    ).strip()


def generate_persistent_names_udev():
    persistent_udev = """\
    {{ generated_header() }}
    #
    # You can modify it, as long as you keep each rule on a single
    # line, and change only the value of the NAME= key.
    {% for iface in interfaces %}

    # PCI device (custom name provided by external tool to mimic Predictable Network Interface Names)
    SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", ATTR{address}=="{{iface.mac}}", ATTR{dev_id}=="0x0", ATTR{type}=="1", NAME="{{iface.name}}"
    {% endfor %}
    """  # noqa
    return {"etc/udev/rules.d/70-persistent-net.rules": persistent_udev}


def generate_persistent_names_mdev():
    mdevconf = """\
        {{ generated_header() }}

        -SUBSYSTEM=net;DEVPATH=.*/net/.*;.*     root:root 600 @/sbin/nameif -s
    """

    mactab = """\
        {{ generated_header() }}

        {% for iface in interfaces %}
        {{ iface.meta_name }} {{ iface.mac }}
        {% endfor %}
    """

    return {"etc/mdev.conf": mdevconf, "etc/mactab": mactab}


def resolvers(default):
    resolvers = ()
    try:
        with open("/etc/resolv.conf") as f:
            reg = re.compile(r"nameserver ([0-9]+(\.[0-9]+){3})$")
            resolvers = tuple(
                [m.group(1) for m in [reg.match(line) for line in f.readlines()] if m]
            )
    except Exception:
        pass
    finally:
        if len(resolvers) == 0:
            resolvers = default

    return resolvers


def get_interfaces():
    # let udev discover the nics, some renaming may take place which is why we
    # don't store the discovered nics
    for nic in discover_nics(get_devices_info()):
        udev_update_db(nic["logicalname"])

    nics = []
    for nic in discover_nics(get_devices_info()):
        lname = nic["logicalname"]
        name = None
        names = {}
        for line in get_udev_info(lname):
            line = line.decode()
            if not line.startswith("E: ID_NET_NAME_"):
                continue
            k, v = line.split()[1].split("=")
            prefix_len = len("ID_NET_NAME_")
            k = k[prefix_len:]
            names[k] = v

        names["LOGICAL"] = lname

        for t in ("ONBOARD", "SLOT", "PATH", "MAC"):
            if t in names:
                name = names[t]
                break

        n = {"names": names, "name": name, "mac": nic["mac"], "driver": nic["driver"]}
        # for test-network.py
        if n["driver"] == "dummy":
            n["name"] = lname

        nics.append(n)
    return nics


def udev_update_db(nic):
    path = "/sys/class/net/" + nic

    # udev needs to discover some of the device properties, we let it do so with
    # the `test` sub-command
    stdout = subprocess.DEVNULL
    stderr = subprocess.PIPE
    ret = subprocess.run(
        ["udevadm", "test", "--action=add", path], stdout=stdout, stderr=stderr
    )
    if ret.returncode:
        print(
            "udevadm test returned an error:",
            ret.stderr.decode(),
            sep="\n",
            file=sys.stderr,
        )

    subprocess.run(["udevadm", "settle"])


def get_udev_info(nic):
    path = "/sys/class/net/" + nic
    return get_output(["udevadm", "info", path]).splitlines()


def get_output(cmd):
    stdout = subprocess.PIPE
    return subprocess.run(cmd, check=True, stdout=stdout).stdout


def get_lshw_info():
    # Workaround for x.large.arm: Skip framebuffer test ("-disable fb")
    return json.loads(get_output(["lshw", "-json", "-disable", "fb"]).decode())


def get_devices_info():
    path = "/sys/class/net/"
    nics = []
    ifaces = os.listdir(path)
    for iface in ifaces:
        try:
            driver_path = os.readlink(path + iface + "/device/driver")
            driver = os.path.basename(driver_path)
        except OSError:
            continue

        with open(path + iface + "/address") as f:
            mac = f.readline().strip()

        n = {"logicalname": iface, "mac": mac, "driver": driver}
        nics.append(n)
    return nics


def pam(arg, *funcs):
    """pam is like map but instead of calling one function with multiple args,
    it calls multiple functions with one arg"""
    return map(lambda f: f(arg), *funcs)


def discover_nics(devs):
    ignored_drivers = ("bridge", "veth", "virtio-pci")
    nics = []

    def is_real_nic(dev):
        return dev["driver"] not in ignored_drivers

    for dev in devs:
        print("name={} driver={}".format(dev["logicalname"], dev["driver"]))

        if is_real_nic(dev):
            nics.append(dev)

    return nics


def get_matched_interfaces(metainterfaces, realinterfaces):
    nics = []

    for metainterface in metainterfaces:
        for realinterface in realinterfaces:
            if metainterface["mac"].lower() == realinterface["mac"].lower():
                d = {}
                d.update(metainterface)
                d.update(realinterface)

                # Expose the original metadata name for alternative implementations
                d["meta_name"] = metainterface.get("name")

                nics.append(d)

    return nics


def log_ip_address(ip, name):
    if ip:
        click.echo(
            "{name}: {ip}\tGateway: {gw}\tNetmask: {nm}".format(
                name=name,
                ip=ip.get("address"),
                gw=ip.get("gateway"),
                nm=ip.get("netmask"),
            )
        )
    else:
        click.echo("{name}: disabled".format(name=name))
