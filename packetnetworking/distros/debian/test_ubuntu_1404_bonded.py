from textwrap import dedent
import pytest


@pytest.fixture
def ubuntu_1404_bonded_network(generic_debian_bonded_network):
    def _builder(**kwargs):
        return generic_debian_bonded_network("ubuntu", 14.04, **kwargs)

    return _builder


def test_ubuntu_1404_public_bonded_task_etc_network_interfaces(
    ubuntu_1404_bonded_network
):
    """Validates /etc/network/interfaces for a public bond"""

    builder = ubuntu_1404_bonded_network(public=True)
    tasks = builder.render()
    result = dedent(
        """\
        auto lo
        iface lo inet loopback

        auto bond0
        iface bond0 inet static
            address {ipv4pub.address}
            netmask {ipv4pub.netmask}
            gateway {ipv4pub.gateway}
            bond-downdelay 200
            bond-miimon 100
            bond-mode {bonding_mode}
            bond-updelay 200
            bond-xmit_hash_policy layer3+4
            bond-lacp-rate 1
            bond-slaves {iface0.name} {iface1.name}
            dns-nameservers {dns1} {dns2}
        iface bond0 inet6 static
            address {ipv6pub.address}
            netmask {ipv6pub.cidr}
            gateway {ipv6pub.gateway}

        auto bond0:0
        iface bond0:0 inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            post-up route add -net 10.0.0.0/8 gw {ipv4priv.gateway}
            post-down route del -net 10.0.0.0/8 gw {ipv4priv.gateway}

        auto {iface0.name}
        iface {iface0.name} inet manual
            bond-master bond0

        auto {iface1.name}
        iface {iface1.name} inet manual
            pre-up sleep 4
            bond-master bond0
    """
    ).format(
        ipv4pub=builder.ipv4pub.first,
        ipv6pub=builder.ipv6pub.first,
        ipv4priv=builder.ipv4priv.first,
        iface0=builder.network.interfaces[0],
        iface1=builder.network.interfaces[1],
        bonding_mode=builder.network.bonding.mode,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/network/interfaces"] == result


def test_ubuntu_1404_private_bonded_task_etc_network_interfaces(
    ubuntu_1404_bonded_network
):
    """
    When no public ip is assigned, we should see the private ip details in the
    /etc/network/interfaces file.
    """
    builder = ubuntu_1404_bonded_network(public=False)
    tasks = builder.render()
    result = dedent(
        """\
        auto lo
        iface lo inet loopback

        auto bond0
        iface bond0 inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            gateway {ipv4priv.gateway}
            bond-downdelay 200
            bond-miimon 100
            bond-mode {bonding_mode}
            bond-updelay 200
            bond-xmit_hash_policy layer3+4
            bond-lacp-rate 1
            bond-slaves {iface0.name} {iface1.name}
            dns-nameservers {dns1} {dns2}


        auto {iface0.name}
        iface {iface0.name} inet manual
            bond-master bond0

        auto {iface1.name}
        iface {iface1.name} inet manual
            pre-up sleep 4
            bond-master bond0
    """
    ).format(
        ipv4priv=builder.ipv4priv.first,
        iface0=builder.network.interfaces[0],
        iface1=builder.network.interfaces[1],
        bonding_mode=builder.network.bonding.mode,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/network/interfaces"] == result


def test_ubuntu_1404_task_etc_modules(ubuntu_1404_bonded_network):
    """Validates /etc/modules for a public bond"""
    builder = ubuntu_1404_bonded_network(public=True)
    tasks = builder.render()
    result = dedent(
        """\
        bonding
    """
    )
    assert tasks["etc/modules"] == result


def test_ubuntu_1404_etc_resolvers_configured(ubuntu_1404_bonded_network, fake):
    """
    Validates /etc/resolv.conf is configured correctly
    """
    builder = ubuntu_1404_bonded_network()
    resolver1 = fake.ipv4()
    resolver2 = fake.ipv4()
    builder.network.resolvers = (resolver1, resolver2)
    tasks = builder.render()
    result = dedent(
        """\
        nameserver {resolver1}
        nameserver {resolver2}
    """
    ).format(resolver1=resolver1, resolver2=resolver2)
    assert tasks["etc/resolv.conf"] == result


def test_ubuntu_1404_etc_hostname_configured(ubuntu_1404_bonded_network):
    """
    Validates /etc/hostname is configured correctly
    """
    builder = ubuntu_1404_bonded_network()
    tasks = builder.render()
    result = dedent(
        """\
        {hostname}
    """
    ).format(hostname=builder.metadata.hostname)
    assert tasks["etc/hostname"] == result


def test_ubuntu_1404_etc_hosts_configured(ubuntu_1404_bonded_network):
    """
    Validates /etc/hosts is configured correctly
    """
    builder = ubuntu_1404_bonded_network()
    tasks = builder.render()
    result = dedent(
        """\
        127.0.0.1	localhost	{hostname}

        # The following lines are desirable for IPv6 capable hosts
        ::1	localhost ip6-localhost ip6-loopback
        ff02::1	ip6-allnodes
        ff02::2	ip6-allrouters
    """
    ).format(hostname=builder.metadata.hostname)
    assert tasks["etc/hosts"] == result


# pylama:ignore=E501
def test_ubuntu_1404_persistent_interface_names(ubuntu_1404_bonded_network):
    """
    When using certain operating systems, we want to bypass driver interface name,
    here we make sure the /etc/udev/rules.d/70-persistent-net.rules is generated.
    """
    builder = ubuntu_1404_bonded_network()
    tasks = builder.render()
    result = dedent(
        """\
        # This file was automatically generated by the packet.net installation environment.
        #
        # You can modify it, as long as you keep each rule on a single
        # line, and change only the value of the NAME= key.

        # PCI device (custom name provided by external tool to mimic Predictable Network Interface Names)
        SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", ATTR{{address}}=="{iface0.mac}", ATTR{{dev_id}}=="0x0", ATTR{{type}}=="1", KERNEL=="e*", NAME="{iface0.name}"

        # PCI device (custom name provided by external tool to mimic Predictable Network Interface Names)
        SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", ATTR{{address}}=="{iface1.mac}", ATTR{{dev_id}}=="0x0", ATTR{{type}}=="1", KERNEL=="e*", NAME="{iface1.name}"
    """
    ).format(iface0=builder.network.interfaces[0], iface1=builder.network.interfaces[1])
    assert tasks["etc/udev/rules.d/70-persistent-net.rules"] == result
