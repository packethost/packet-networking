from textwrap import dedent
from .conftest import versions
import pytest


@pytest.fixture
def individual_network_builder(generic_debian_individual_network):
    def _builder(distro, version, **kwargs):
        return generic_debian_individual_network(distro, version, **kwargs)

    return _builder


@pytest.mark.parametrize("distro,version", versions)
def test_public_individual_task_etc_network_interfaces(
    individual_network_builder, distro, version
):
    """Validates /etc/network/interfaces for a public bond"""

    builder = individual_network_builder(distro, version, public=True)
    tasks = builder.render()

    iface0 = builder.network.interfaces[0].name
    ipv4priv = builder.ipv4priv.first
    ipv4pub = builder.ipv4pub.first
    ipv6pub = builder.ipv6pub.first
    result = f"""\
        auto lo
        iface lo inet loopback

        auto {iface0}
        iface {iface0} inet static
            address {ipv4pub.address}
            netmask {ipv4pub.netmask}
            gateway {ipv4pub.gateway}
            dns-nameservers {" ".join(sorted(builder.network.resolvers))}

        iface {iface0} inet6 static
            address {ipv6pub.address}
            netmask {ipv6pub.cidr}
            gateway {ipv6pub.gateway}

        auto {iface0}:0
        iface {iface0}:0 inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            post-up route add -net 10.0.0.0/8 gw {ipv4priv.gateway}
            post-down route del -net 10.0.0.0/8 gw {ipv4priv.gateway}
        """
    assert tasks["etc/network/interfaces"] == dedent(result)


@pytest.mark.parametrize("distro,version", versions)
def test_private_individual_task_etc_network_interfaces(
    individual_network_builder, distro, version
):
    """
    When no public ip is assigned, we should see the private ip details in the
    /etc/network/interfaces file.
    """
    builder = individual_network_builder(distro, version, public=False)
    tasks = builder.render()

    iface0 = builder.network.interfaces[0].name
    ipv4priv = builder.ipv4priv.first
    result = f"""\
        auto lo
        iface lo inet loopback

        auto {iface0}
        iface {iface0} inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            gateway {ipv4priv.gateway}
            dns-nameservers {" ".join(sorted(builder.network.resolvers))}
        """
    assert tasks["etc/network/interfaces"] == dedent(result)


@pytest.mark.parametrize("distro,version", versions)
def test_public_individual_task_etc_network_interfaces_with_custom_private_ip_space(
    individual_network_builder, distro, version
):
    """Validates /etc/network/interfaces for a public bond"""
    subnets = {"private_subnets": reversed(["192.168.5.0/24", "172.16.0.0/12"])}
    builder = individual_network_builder(distro, version, public=True, metadata=subnets)
    tasks = builder.render()

    iface0 = builder.network.interfaces[0].name
    ipv4priv = builder.ipv4priv.first
    ipv4pub = builder.ipv4pub.first
    ipv6pub = builder.ipv6pub.first
    result = f"""\
        auto lo
        iface lo inet loopback

        auto {iface0}
        iface {iface0} inet static
            address {ipv4pub.address}
            netmask {ipv4pub.netmask}
            gateway {ipv4pub.gateway}
            dns-nameservers {" ".join(sorted(builder.network.resolvers))}

        iface {iface0} inet6 static
            address {ipv6pub.address}
            netmask {ipv6pub.cidr}
            gateway {ipv6pub.gateway}

        auto {iface0}:0
        iface {iface0}:0 inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            post-up route add -net 172.16.0.0/12 gw {ipv4priv.gateway}
            post-down route del -net 172.16.0.0/12 gw {ipv4priv.gateway}
            post-up route add -net 192.168.5.0/24 gw {ipv4priv.gateway}
            post-down route del -net 192.168.5.0/24 gw {ipv4priv.gateway}
        """
    assert tasks["etc/network/interfaces"] == dedent(result)


@pytest.mark.parametrize("distro,version", versions)
def test_private_individual_task_etc_network_interfaces_with_custom_private_ip_space(
    individual_network_builder, distro, version
):
    """
    When no public ip is assigned, we should see the private ip details in the
    /etc/network/interfaces file.
    """
    builder = individual_network_builder(distro, version, public=False)
    tasks = builder.render()

    iface0 = builder.network.interfaces[0].name
    ipv4priv = builder.ipv4priv.first
    result = f"""\
        auto lo
        iface lo inet loopback

        auto {iface0}
        iface {iface0} inet static
            address {ipv4priv.address}
            netmask {ipv4priv.netmask}
            gateway {ipv4priv.gateway}
            dns-nameservers {" ".join(sorted(builder.network.resolvers))}
    """
    assert tasks["etc/network/interfaces"] == dedent(result)


@pytest.mark.parametrize("distro,version", versions)
def test_dns_resolver_configured(individual_network_builder, fake, distro, version):
    """
    Validates either /etc/resolv.conf or /etc/systemd/resolved.conf is configured correctly
    """
    builder = individual_network_builder(distro, version)
    resolver1 = fake.ipv4()
    resolver2 = fake.ipv4()
    builder.network.resolvers = (resolver1, resolver2)
    tasks = builder.render()

    if distro == "ubuntu":
        result = f"""\
            [Resolve]
            DNS={resolver1} {resolver2}
            """
        assert tasks["etc/systemd/resolved.conf"] == dedent(result)
        assert "etc/resolv.conf" not in tasks
    else:
        result = f"""\
            nameserver {resolver1}
            nameserver {resolver2}
        """
        assert tasks["etc/resolv.conf"] == dedent(result)


@pytest.mark.parametrize("distro,version", versions)
def test_etc_hostname_configured(individual_network_builder, distro, version):
    """
    Validates /etc/hostname is configured correctly
    """
    builder = individual_network_builder(distro, version)
    tasks = builder.render()

    hostname = builder.metadata.hostname
    result = f"{hostname}\n"
    assert tasks["etc/hostname"] == result


@pytest.mark.parametrize("distro,version", versions)
def test_etc_hosts_configured(individual_network_builder, distro, version):
    """
    Validates /etc/hosts is configured correctly
    """
    builder = individual_network_builder(distro, version)
    tasks = builder.render()

    hostname = builder.metadata.hostname
    result = f"""\
        127.0.0.1	localhost	{hostname}

        # The following lines are desirable for IPv6 capable hosts
        ::1	localhost ip6-localhost ip6-loopback
        ff02::1	ip6-allnodes
        ff02::2	ip6-allrouters
        """
    assert tasks["etc/hosts"] == dedent(result)


@pytest.mark.parametrize("distro,version", versions)
def test_persistent_interface_names(individual_network_builder, distro, version):
    """
    When using certain operating systems, we want to bypass driver interface name,
    here we make sure the /etc/udev/rules.d/70-persistent-net.rules is generated.
    """
    builder = individual_network_builder(distro, version)
    tasks = builder.render()

    partial = """\
        # This file was automatically generated by the Equinix Metal installation environment.
        # See https://github.com/packethost/packet-networking for details.
        #
        # You can modify it, as long as you keep each rule on a single
        # line, and change only the value of the NAME= key.
        """
    result = dedent(partial)

    for iface in builder.network.interfaces:
        partial = f"""
            # PCI device (custom name provided by external tool to mimic Predictable Network Interface Names)
            SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", ATTR{{address}}=="{iface.mac}", ATTR{{dev_id}}=="0x0", ATTR{{type}}=="1", NAME="{iface.name}"
            """
        result += dedent(partial)

    if distro == "debian" and version == "12":
        assert "etc/udev/rules.d/70-persistent-net.rules" not in tasks
    else:
        assert tasks["etc/udev/rules.d/70-persistent-net.rules"] == result


@pytest.mark.parametrize("distro,version", versions)
def test_public_individual_dhcp_task_etc_network_interfaces(
    individual_network_builder,
    make_interfaces_dhcp_metadata,
    distro,
    version,
):
    """Validates /etc/network/interfaces for a public dhcp interfaces"""

    builder = individual_network_builder(
        distro, version, public=True, post_gen_metadata=make_interfaces_dhcp_metadata
    )
    tasks = builder.render()

    partial = """\
        auto lo
        iface lo inet loopback
        """
    result = dedent(partial)

    for iface in builder.network.interfaces:
        partial = f"""
        auto {iface.name}
        iface {iface.name} inet dhcp
        """
        result += dedent(partial)

    result += "\n"
    assert tasks["etc/network/interfaces"] == result
