from netaddr import IPNetwork
import copy
import mock
import faker
import pytest
import random
from .metadata import Metadata


@pytest.fixture
def fake():
    return faker.Faker()


@pytest.fixture
def patch_dict():
    def _patch_dict(orig, updates):
        for k, v in updates.items():
            delete = str(k).startswith("-")
            replace = str(k).startswith("!")
            if delete or replace:
                k = k[1:]
            if delete:
                del orig[k]
                continue
            if k not in orig or replace:
                orig[k] = v
            elif isinstance(orig[k], dict) and isinstance(v, dict):
                _patch_dict(orig[k], v)
            elif isinstance(orig[k], list) and (
                isinstance(v, list) or isinstance(v, dict)
            ):
                _patch_list(orig[k], v)
            else:
                orig[k] = v
        return orig

    def _patch_list(orig, updates):
        if isinstance(updates, list):
            updates = {i: updates[i] for i in range(len(updates))}
        for k, v in updates.items():
            delete = str(k).startswith("-")
            replace = str(k).startswith("!")
            if delete or replace:
                k = int(k[1:])
            if delete:
                del orig[k]
                continue
            if k >= len(orig) or replace:
                orig += [None] * (k - len(orig) + 1)
                orig[k] = v
            elif isinstance(orig[k], list) and (
                isinstance(v, list) or isinstance(v, dict)
            ):
                _patch_list(orig[k], v)
            elif isinstance(orig[k], dict) and isinstance(v, dict):
                _patch_dict(orig[k], v)
            else:
                orig[k] = v
        return orig

    return _patch_dict


@pytest.fixture
def fake_address(fake, patch_dict):
    def _fake_address(**opts):
        address = patch_dict(
            {
                "address": None,
                "address_family": 4,
                "cidr": None,
                "gateway": None,
                "management": True,
                "netmask": None,
                "network": None,
                "public": True,
            },
            opts,
        )
        if address["address"]:
            ip = address["address"]
        elif address["address_family"] == 4:
            ip = fake.ipv4(private=not address["public"])
            if not address["cidr"]:
                address["cidr"] = 31
        else:
            ip = fake.ipv6()
            if not address["cidr"]:
                address["cidr"] = 127
        network = IPNetwork("{}/{}".format(ip, address["cidr"]))
        gw_index = 0 if address["cidr"] in [31, 127] else 1
        address["netmask"] = str(network.netmask)
        address["network"] = str(network[0])
        address["gateway"] = str(network[gw_index])
        if not address["address"]:
            address["address"] = str(network[gw_index + 1])
        return address

    return _fake_address


plan_slugs = (
    "c1.small.x86",
    "c2.medium.x86",
    "c3.medium.x86",
    "g2.large.x86",
    "m2.xlarge.x86",
    "n2.xlarge.x86",
    "x2.xlarge.x86",
)


@pytest.fixture
def metadata(fake, fake_address, patch_dict):
    def _metadata(options, public=True):
        addresses = []
        if public:
            addresses.append(fake_address())
            addresses.append(fake_address(management=False))
            addresses.append(
                fake_address(
                    management=False,
                    address_family=6,
                    netmask="ffff:ffff:ffff:ffff:ffff:ffff:ffff:fffe",
                )
            )
        addresses.append(fake_address(public=False))

        return Metadata(
            patch_dict(
                {
                    "hostname": fake.hostname(),
                    "id": fake.uuid4(),
                    "plan": random.choice(plan_slugs),
                    "network": {
                        "bonding": {"mode": 4},
                        "interfaces": None,
                        "addresses": addresses,
                    },
                },
                options,
            )
        )

    return _metadata


@pytest.fixture
def mockit():
    def _mockit(i, *args, **kwargs):
        return mock.patch(i.__module__ + "." + i.__name__, *args, **kwargs)

    return _mockit
