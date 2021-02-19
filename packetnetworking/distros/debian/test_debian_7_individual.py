from textwrap import dedent
import pytest


@pytest.fixture
def debian_7_individual_network(generic_debian_individual_network):
    def _builder(**kwargs):
        return generic_debian_individual_network("debian", "7", **kwargs)

    return _builder


def test_debian_7_public_individual_task_etc_network_interfaces(
    debian_7_individual_network,
):
    """Validates /etc/network/interfaces for a public bond"""

    builder = debian_7_individual_network(public=True)
    tasks = builder.render()
    result = dedent(
        """\
        auto lo
        iface lo inet loopback

        auto enp0
        iface enp0 inet static
            address {ipv4pub.address}
            netmask {ipv4pub.netmask}
            gateway {ipv4pub.gateway}

            dns-nameservers {dns1} {dns2}
        iface enp0 inet6 static
            address {ipv6pub.address}
            netmask {ipv6pub.cidr}
            gateway {ipv6pub.gateway}

        auto enp0:0
        iface enp0:0 inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            post-up route add -net 10.0.0.0/8 gw {ipv4priv.gateway}
            post-down route del -net 10.0.0.0/8 gw {ipv4priv.gateway}
    """
    ).format(
        ipv4pub=builder.ipv4pub.first,
        ipv6pub=builder.ipv6pub.first,
        ipv4priv=builder.ipv4priv.first,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/network/interfaces"] == result


def test_debian_7_private_individual_task_etc_network_interfaces(
    debian_7_individual_network,
):
    """
    When no public ip is assigned, we should see the private ip details in the
    /etc/network/interfaces file.
    """
    builder = debian_7_individual_network(public=False)
    tasks = builder.render()
    result = dedent(
        """\
        auto lo
        iface lo inet loopback

        auto enp0
        iface enp0 inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            gateway {ipv4priv.gateway}

            dns-nameservers {dns1} {dns2}

    """
    ).format(
        ipv4priv=builder.ipv4priv.first,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/network/interfaces"] == result


# pylama:ignore=E501
def test_debian_7_public_individual_task_etc_network_interfaces_with_custom_private_ip_space(
    debian_7_individual_network,
):
    """Validates /etc/network/interfaces for a public bond"""
    subnets = {"private_subnets": ["192.168.5.0/24", "172.16.0.0/12"]}
    builder = debian_7_individual_network(public=True, metadata=subnets)
    tasks = builder.render()
    result = dedent(
        """\
        auto lo
        iface lo inet loopback

        auto enp0
        iface enp0 inet static
            address {ipv4pub.address}
            netmask {ipv4pub.netmask}
            gateway {ipv4pub.gateway}

            dns-nameservers {dns1} {dns2}
        iface enp0 inet6 static
            address {ipv6pub.address}
            netmask {ipv6pub.cidr}
            gateway {ipv6pub.gateway}

        auto enp0:0
        iface enp0:0 inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            post-up route add -net 192.168.5.0/24 gw {ipv4priv.gateway}
            post-down route del -net 192.168.5.0/24 gw {ipv4priv.gateway}
            post-up route add -net 172.16.0.0/12 gw {ipv4priv.gateway}
            post-down route del -net 172.16.0.0/12 gw {ipv4priv.gateway}
    """
    ).format(
        ipv4pub=builder.ipv4pub.first,
        ipv6pub=builder.ipv6pub.first,
        ipv4priv=builder.ipv4priv.first,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/network/interfaces"] == result


def test_debian_7_private_individual_task_etc_network_interfaces_with_custom_private_ip_space(
    debian_7_individual_network,
):
    """
    When no public ip is assigned, we should see the private ip details in the
    /etc/network/interfaces file.
    """
    subnets = {"private_subnets": ["192.168.5.0/24", "172.16.0.0/12"]}
    builder = debian_7_individual_network(public=False, metadata=subnets)
    tasks = builder.render()
    result = dedent(
        """\
        auto lo
        iface lo inet loopback

        auto enp0
        iface enp0 inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            gateway {ipv4priv.gateway}

            dns-nameservers {dns1} {dns2}

    """
    ).format(
        ipv4priv=builder.ipv4priv.first,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/network/interfaces"] == result


def test_debian_7_etc_resolvers_configured(debian_7_individual_network, fake):
    """
    Validates /etc/resolv.conf is configured correctly
    """
    builder = debian_7_individual_network()
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


def test_debian_7_etc_hostname_configured(debian_7_individual_network):
    """
    Validates /etc/hostname is configured correctly
    """
    builder = debian_7_individual_network()
    tasks = builder.render()
    result = dedent(
        """\
        {hostname}
    """
    ).format(hostname=builder.metadata.hostname)
    assert tasks["etc/hostname"] == result


def test_debian_7_etc_hosts_configured(debian_7_individual_network):
    """
    Validates /etc/hosts is configured correctly
    """
    builder = debian_7_individual_network()
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


def test_debian_7_no_persistent_interface_names(debian_7_individual_network):
    """
    When using certain operating systems, we want to bypass driver interface name,
    here we make sure the /etc/udev/rules.d/70-persistent-net.rules is generated.
    """
    builder = debian_7_individual_network()
    tasks = builder.render()
    assert "etc/udev/rules.d/70-persistent-net.rules" not in tasks
