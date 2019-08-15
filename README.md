# Packet Networking

This is a tool to replace the `network.py` file in [OSIE](https://github.com/packethost/osie) by breaking out the
network configurations into sub packages.

## Requirements

- `python` version `3.5` or higher
- `pip`
- `lshw` version `B.02.18` or higher

## Installation

```shell
pip3 install packet-networking
```

## Usage

```shell
# packet-networking --help
Usage: packet-networking [OPTIONS]

Options:
  --metadata-file FILENAME     Load metadata from a file rather than a URL
  --metadata-url TEXT          URL to download metadata from
  -o, --operating-system TEXT  Operating System and version (ex: centos 7)
                               [required]
  --rootfs PATH                Path to root filesystem  [required]
  -v, --verbose                Provide more detailed output
  -q, --quiet                  Silences all output
  --help                       Show this message and exit.
```

By default `--metadata-url` points to `http://metadata.packet.net/metadata`.

Additionally, if `--metadata-file` is specified, it will override the
`--metadata-url`.

## Example

```
# packet-networking --metadata-file /tmp/metadata.json -o 'centos 7' --rootfs /tmp/rootfs -vvv
DEBUG:packetnetworking:Metadata file '/tmp/metadata.json' specified, preferring over metadata url.
name=ens33 driver=e1000     
name=veth1cb3c99 driver=veth
name=vethe927707 driver=veth
name=virbr0-nic driver=tun
name=virbr0 driver=bridge
name=vethab8fe13 driver=veth
name=br-9ffe68216dc5 driver=bridge
name=veth2dd8fc1 driver=veth
name=docker0 driver=bridge
name=ens33 driver=e1000     
name=veth1cb3c99 driver=veth
name=vethe927707 driver=veth
name=virbr0-nic driver=tun
name=virbr0 driver=bridge
name=vethab8fe13 driver=veth
name=br-9ffe68216dc5 driver=bridge
name=veth2dd8fc1 driver=veth
name=docker0 driver=bridge
DEBUG:root:Processing task: 'etc/resolv.conf'
DEBUG:root:Processing task: 'etc/systemd/system/multi-user.target.wants/NetworkManager.service'
DEBUG:root:Processing task: 'etc/sysconfig/network-scripts/ifcfg-bond0:0'
DEBUG:root:Processing task: 'etc/sysconfig/network-scripts/route-bond0'
DEBUG:root:Processing task: 'etc/modprobe.d/bonding.conf'
DEBUG:root:Processing task: 'etc/systemd/system/dbus-org.freedesktop.nm-dispatcher.service'
DEBUG:root:Processing task: 'etc/hostname'
DEBUG:root:Processing task: 'etc/hosts'
DEBUG:root:Processing task: 'etc/sysconfig/network-scripts/ifcfg-bond0'
DEBUG:root:Processing task: 'etc/sysconfig/network'
DEBUG:root:Processing task: 'etc/systemd/system/dbus-org.freedesktop.NetworkManager.service'
DEBUG:root:Processing task: 'sbin/ifup-pre-local'
DEBUG:root:Processing task: 'etc/sysconfig/network-scripts/ifcfg-ens33'
Configuration files written to root filesystem '/tmp/rootfs'
```

Here is an example of the files created

```
# find /tmp/rootfs/
/tmp/rootfs/
/tmp/rootfs/etc
/tmp/rootfs/etc/modprobe.d
/tmp/rootfs/etc/modprobe.d/bonding.conf
/tmp/rootfs/etc/sysconfig
/tmp/rootfs/etc/sysconfig/network-scripts
/tmp/rootfs/etc/sysconfig/network-scripts/ifcfg-bond0
/tmp/rootfs/etc/sysconfig/network-scripts/ifcfg-ens33
/tmp/rootfs/etc/sysconfig/network-scripts/ifcfg-bond0:0
/tmp/rootfs/etc/sysconfig/network-scripts/route-bond0
/tmp/rootfs/etc/sysconfig/network
/tmp/rootfs/etc/hosts
/tmp/rootfs/etc/hostname
/tmp/rootfs/etc/resolv.conf
/tmp/rootfs/sbin
/tmp/rootfs/sbin/ifup-pre-local
```

# Extending and manipulating data

## Distro Builders

Currently each distro family has their own distro builder. For instance, the
[debian builder](packetnetworking/distros/debian) encompasses both Debian and
Ubuntu distros. For the redhat family of distros, RedHat, CentOS and Scientific
Linux are all under the [redhat builder](packetnetworking/distros/redhat).

Each distro has a Distro Builder that defines which os's it supports along with
the different Network Builder classes it can implement. Below is a snippet of the
`DebianBuilder`

```python
class DebianBuilder(DistroBuilder):
    distros = ["debian", "ubuntu"]
    network_builders = [DebianBondedNetwork]
```

Here we can see both Debian and Ubuntu distros are supported, and the only
supported network builder is a bonded configuration.

## Network Builders

At the moment, the only supported network configuration at packet is a bonded
configuration. In the future will be able to add more network builders to support
different network configurations.

Here is a small snippet of the the [DebianBondedNetwork](packetnetworking/distros/debian/debian_bonded_networking.py),
some lines have been removed for brevity.

```python
class DebianBondedNetwork(NetworkBuilder):
    def build(self):
        self.build_tasks()

    def build_tasks(self):
        self.tasks = {}
        self.tasks[
            "etc/network/interfaces"
        ] = """\
            auto lo
            iface lo inet loopback

            auto bond0
            iface bond0 inet static
                {% if ip4pub %}
                address {{ ip4pub.address }}
                netmask {{ ip4pub.netmask }}
                gateway {{ ip4pub.gateway }}
                {% else %}
                address {{ ip4priv.address }}
                netmask {{ ip4priv.netmask }}
                gateway {{ ip4priv.gateway }}
                {% endif %}
        """

        self.tasks[
            "etc/resolv.conf"
        ] = """\
            {% for server in resolvers %}
            nameserver {{ server }}
            {% endfor %}
        """

        return self.tasks
```

Currently, since the bonded network is the only configuration, we can simply call
`build_tasks` from the `build` method. However in future we could add some
conditions to run the `build_tasks` method if necessary.

`build_tasks` simple adds all the templates for each file to a dictionary that
will later be processed by the [Network Builder](packetnetworking/distros/network_builder.py)'s
`render` method. Render will render each template and return the updated task
list. The render function is called from within the `run` method, which after
receiving the rendered tasks, will actually write or delete the files.

## Hooks

In some instances, we need to modify the data before we process the builders.
One of these instances are for plans which should only have a single interface,
we want to make sure we only pass a single interface along to the builders.

For this we have a **hook** system. You can define a class which inherits the
`BuilderHook` class and define one or more hooks in that class.

For the above example where we should only have a single interface, a hook
can be created after initalization (`initialized`). You can view the full
code at [hooks/single_interface_hook.py](packetnetworking/hooks/single_interface_hook.py).
However, here is a snippet.

```python
class SingleInterfaceHook(BuilderHook):
    plans = ["baremetal_1e", "x1.small.x86"]

    def hook_initialized(self, builder):
        if builder.metadata.plan.lower() in self.plans:
            builder.network.interfaces = builder.network.interfaces[:1]
```

After defining a new hook, simply import it and add it to the `__all__` variable
in [hooks/\_\_init\_\_.py](packetnetworking/hooks/__init__.py) and you're ready
to go.

Each time a hook is triggered, a new instance of the class will be created and
the the corresponding `hook_*` function will be executed. The first argument
passed to each hook function is the `Builder` instance. This contains the
metadata and the initalized network details.

Triggers can define additional arguments and keyword arguments that will be
passed to each hook triggered.

## Running Tests

```
git clone git@github.com:packethost/packet-networking.git
cd packet-networking/
pip3 install -e .[test]
py.test packetnetworking
```

**Example Output:**

```
# py.test packetnetworking
===================================== test session starts ======================================
platform linux -- Python 3.5.2, pytest-5.0.1, py-1.8.0, pluggy-0.12.0
rootdir: /home/packet/packet-networking
collected 3 items                                                                              

packetnetworking/distros/redhat/test_bonded.py ...                                       [100%]

=================================== 3 passed in 0.13 seconds ===================================
```