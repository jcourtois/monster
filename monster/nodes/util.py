import logging
import time
import chef

import monster.active as active

logger = logging.getLogger(__name__)


def node_names():
    """Helper for naming nodes.
    :rtype: list(str)
    """
    try:
        return _names_defined_in_template()
    except (KeyError, AssertionError):
        return _generated_names_from_roles()


def _names_defined_in_template():
    """Returns list of template node names, if they exist.
    Each node must have a unique name defined in the template."""
    names = [node['hostname'] for node in active.template['nodes']]
    assert len(set(names)) == len(names)
    return names


def _generated_names_from_roles():
    import collections
    prefix = active.build_args['name']
    roles = [node['features'][0] for node in active.template['nodes']]
    count = collections.Counter()
    names = []
    for role in roles:
        count[role] += 1
        names.append("%s-%s%s" % (prefix, role, count[role]))
    return names


def node_search(query, environment=None, tries=10):
    """Performs a node search query on the chef server.
    :param query: search query to request
    :type query: string
    :param environment: Environment the query should be
    :type environment: monster.environments.chef.environment.Environment
    :rtype: Iterator (chef.Node)
    """
    if environment:
        api = environment.local_api
    else:
        api = chef.autoconfigure()
    search = None
    while not search and tries > 0:
        search = chef.Search("node", api=api).query(query)
        time.sleep(10)
        tries -= 1
    return (n.object for n in search)


class OS:
    @staticmethod
    def commands(os_name):
        """Given the name of an OS, returns an object that is capable of
        providing OS specific command-line commands for many useful
        functionalities, such as package upgrades."""
        if os_name in ['ubuntu']:
            return OS.DebianOS()
        elif os_name in ['rhel', 'centos']:
            return OS.RHEL()
        else:
            logger.exception("OS not supported at this time!")

    class DebianOS(object):
        def check_package(self, package):
            return "dpkg -l | grep {0}".format(package)

        def update_dist(self, dist_upgrade=False):
            if dist_upgrade:
                return 'apt-get update; apt-get dist-upgrade -y'
            else:
                return 'apt-get update; apt-get upgrade -y'

        def install_package(self, package):
            return 'apt-get install -y {0}'.format(package)

        def remove_chef(self):
            return "apt-get remove --purge -y chef; rm -rf /etc/chef"

    class RHEL(object):
        def check_package(self, package):
            return "rpm -a | grep {0}".format(package)

        def update_dist(self, dist_upgrade=False):
            return 'yum update -y'

        def install_package(self, package):
            return 'yum install -y {0}'.format(package)

        def remove_chef(self):
            return "yum remove -y chef; rm -rf /etc/chef /var/chef"
