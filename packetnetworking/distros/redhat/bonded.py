from .. import NetworkBuilder
import os


class RedhatBondedNetwork(NetworkBuilder):
    def build(self, osinfo):
        self.build_tasks(osinfo)

    def build_tasks(self, osinfo):
        self.tasks = {}
        self.tasks[
            "etc/sysconfig/network"
        ] = """\
            NETWORKING=yes
            HOSTNAME={{ hostname }}
            {% if ip4pub %}
            GATEWAY={{ ip4pub.gateway }}
            {% else %}
            GATEWAY={{ ip4priv.gateway }}
            {% endif %}
            GATEWAYDEV=bond0
            NOZEROCONF=yes
        """

        self.tasks[
            "etc/modprobe.d/bonding.conf"
        ] = """\
            alias bond0 bonding
            options bond0 mode={{ net.bonding.mode }} miimon=100 downdelay=200 updelay=200 xmit_hash_policy=layer3+4 lacp_rate=1
        """

        self.tasks[
            "etc/sysconfig/network-scripts/ifcfg-bond0"
        ] = """\
            DEVICE=bond0
            NAME=bond0
            {% if ip4pub %}
            IPADDR={{ ip4pub.address }}
            NETMASK={{ ip4pub.netmask }}
            GATEWAY={{ ip4pub.gateway }}
            {% else %}
            IPADDR={{ ip4priv.address }}
            NETMASK={{ ip4priv.netmask }}
            GATEWAY={{ ip4priv.gateway }}
            {% endif %}
            BOOTPROTO=none
            ONBOOT=yes
            USERCTL=no
            TYPE=Bond
            BONDING_OPTS="mode={{ net.bonding.mode }} miimon=100 downdelay=200 updelay=200"

            {% if ip6pub %}
            IPV6INIT=yes
            IPV6ADDR={{ ip6pub.address }}/{{ ip6pub.cidr }}
            IPV6_DEFAULTGW={{ ip6pub.gateway }}
            {% endif %}
            {% for dns in resolvers %}
            DNS{{ loop.index }}={{ dns }}
            {% endfor %}
        """

        if self.ipv4pub:
            self.tasks[
                "etc/sysconfig/network-scripts/ifcfg-bond0:0"
            ] = """\
                DEVICE=bond0:0
                NAME=bond0:0
                IPADDR={{ ip4priv.address }}
                NETMASK={{ ip4priv.netmask }}
                GATEWAY={{ ip4priv.gateway }}
                BOOTPROTO=none
                ONBOOT=yes
                USERCTL=no
                {% for dns in resolvers %}
                DNS{{ loop.index }}={{ dns }}
                {% endfor %}
            """

            # If no ip4pub is specified, the ip4priv is configured on the bond0 interface
            # so there is no need to add the custom route
            self.tasks[
                "etc/sysconfig/network-scripts/route-bond0"
            ] = """\
                10.0.0.0/8 via {{ ip4priv.gateway }} dev bond0:0
            """

        ifcfg = """\
            DEVICE={iface}
            ONBOOT=yes
            HWADDR={{{{ interfaces[{i}].mac }}}}
            MASTER=bond0
            SLAVE=yes
            BOOTPROTO=none
        """
        for i in range(len(self.network.interfaces)):
            name = self.network.interfaces[i]["name"]
            cfg = ifcfg.format(iface=name, i=i)
            self.tasks["etc/sysconfig/network-scripts/ifcfg-" + name] = cfg

        self.tasks[
            "etc/resolv.conf"
        ] = """\
            {% for server in resolvers %}
            nameserver {{ server }}
            {% endfor %}
        """

        self.tasks[
            "etc/hostname"
        ] = """\
            {{ hostname }}
        """

        self.tasks["etc/hosts"] = (
            "127.0.0.1   localhost localhost.localdomain localhost4 "
            + "localhost4.localdomain4\n"
            + "::1         localhost localhost.localdomain localhost6 "
            + "localhost6.localdomain6\n"
        )

        ifup_pre_local = """\
            #!/bin/bash

            set -o errexit -o nounset -o pipefail -o xtrace

            iface=${1#*-}
            case "$iface" in
            bond0 | {{interfaces[0].name}}) ip link set "$iface" address {{interfaces[0].mac}} ;;
            {% for iface in interfaces[1:] %}
                    {{iface.name}}) ip link set "$iface" address {{iface.mac}} && sleep 4 ;;
            {% endfor %}
            *) echo "ignoring unknown interface $iface" && exit 0 ;;
            esac
        """  # noqa

        self.tasks["sbin/ifup-pre-local"] = {"template": ifup_pre_local, "mode": 0o755}

        if osinfo.name not in ("scientificcernslc", "redhatenterpriseserver"):
            for service in (
                "dbus-org.freedesktop.NetworkManager",
                "dbus-org.freedesktop.nm-dispatcher",
                "multi-user.target.wants/NetworkManager",
            ):
                self.tasks[
                    os.path.join("etc/systemd/system", service + ".service")
                ] = None
        else:
            self.tasks.update(generate_persistent_names())
        return self.tasks
