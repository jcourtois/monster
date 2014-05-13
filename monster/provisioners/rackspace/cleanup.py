import chef

import monster.provisioners.rackspace.provisioner as rackspace
import monster.database as database
from monster.nodes.util import node_names

#TODO: (james) Currently, this safe-deletion implementation is specific to
#the Rackspace provisioner.  This could be clearer and more decoupled.
local_api = chef.autoconfigure()


def _delete_node(name):
    provisioner = rackspace.Provisioner()
    node = chef.Node(name, local_api)
    if node.exists:
        provisioner.compute_client.servers.get(node['uuid']).delete()
        node.delete()


def _delete_client(name):
    client = chef.Client(name, local_api)
    if client.exists:
        client.delete()


def _delete_env(build_name):
    env = chef.Environment(build_name, local_api)
    if env.exists:
        env.delete()


def force_destroy_deployment(build_name):
    """Manually walks through the destruction of a rpcs chef deployment."""
    for name in node_names():
        _delete_node(name)
        _delete_client(name)
    _delete_env(build_name)
    database.remove_key(build_name)
