from time import sleep

from monster import util
from monster.upgrades.upgrade import Upgrade


class FourTwoOne(Upgrade):
    """
    4.2.1 Upgrade Procedures
    """

    def __init__(self, deployment):
        super(FourTwoOne, self).__init__(deployment)

    def prepare_upgrade(self):
        """
        Prepares a 4.2.1 upgrade with mungerator
        """
        controllers = list(self.deployment.search_role('controller'))
        computes = list(self.deployment.search_role('compute'))
        controller1 = controllers[0]
        controller2 = None

        chef_server = next(self.deployment.search_role('chefserver'))
        # purge cookbooks
        munge = ["for i in /var/chef/cache/cookbooks/*; do rm -rf $i; done"]
        ncmds = []
        ccmds = []
        controller1.add_run_list_item(['role[heat-all]'])
        if self.deployment.feature_in('highavailability'):
            controller2 = controllers[1]
            controller2.add_run_list_item(['role[heat-api]',
                                           'role[heat-api-cfn]',
                                           'role[heat-api-cloudwatch]'])
        if self.deployment.os_name == "precise":
            # For Ceilometer
            ncmds.extend([
                "apt-get clean",
                "apt-get -y install python-warlock python-novaclient babel"])
            # For Horizon
            ccmds.append(
                "apt-get -y install openstack-dashboard python-django-horizon")
            # For mungerator
            munge.extend(["apt-get -y install python-dev",
                          "apt-get -y install python-setuptools"])
            # For QEMU
            provisioner = str(self.deployment.provisioner)
            if provisioner == "rackspace" or provisioner == "openstack":
                ncmds.extend(
                    ["apt-get update",
                     "apt-get remove qemu-utils -y",
                     "apt-get install qemu-utils -y"])

        if self.deployment.os_name == "centos":
            # For mungerator
            munge.extend(["yum install -y openssl-devel",
                          "yum install -y python-devel",
                          "yum install -y python-setuptools"])

        node_commands = "; ".join(ncmds)
        controller_commands = "; ".join(ccmds)
        for controller in controllers:
            controller.run_cmd(node_commands)
            controller.run_cmd(controller_commands)
        for compute in computes:
            compute.run_cmd(node_commands)

        # backup db
        backup = util.config['upgrade']['commands']['backup-db']
        controller1.run_cmd(backup)

        # Munge away quantum
        munge_dir = "/opt/upgrade/mungerator"
        munge_repo = "https://github.com/rcbops/mungerator"
        munge.extend([
            "rm -rf {0}".format(munge_dir),
            "git clone {0} {1}".format(munge_repo, munge_dir),
            "cd {0}; python setup.py install".format(munge_dir),
            "mungerator munger --client-key /etc/chef-server/admin.pem "
            "--auth-url https://127.0.0.1:443 all-nodes-in-env "
            "--name {0}".format(self.deployment.name)])
        chef_server.run_cmd("; ".join(munge))
        self.deployment.environment.save_locally()

    def upgrade(self, rc=False):
        """
        Upgrades the deployment (very chefy, rcbopsy)
        """

        if rc:
            upgrade_branch = "v4.2.1rc"
        else:
            upgrade_branch = "v4.2.1"

        supported = util.config['upgrade']['supported'][self.deployment.branch]
        if upgrade_branch not in supported:
            util.logger.error("{0} to {1} upgarde not supported".format(
                self.deployment.branch, upgrade_branch))
            raise NotImplementedError

        # prepare the upgrade
        self.prepare_upgrade()

        # Gather all the nodes of the deployment
        chef_server = next(self.deployment.search_role('chefserver'))
        controllers = list(self.deployment.search_role('controller'))
        computes = list(self.deployment.search_role('compute'))

        # upgrade the chef server
        self.deployment.branch = upgrade_branch

        controllers = list(self.deployment.search_role('controller'))
        computes = list(self.deployment.search_role('compute'))
        controller1 = controllers[0]
        controller2 = None

        chef_server = next(self.deployment.search_role('chefserver'))
        # purge cookbooks
        munge = ["for i in /var/chef/cache/cookbooks/*; do rm -rf $i; done"]
        ncmds = []
        ccmds = []
        controller1.add_run_list_item(['role[heat-all]'])
        if self.deployment.feature_in('highavailability'):
            controller2 = controllers[1]
            controller2.add_run_list_item(['role[heat-api]',
                                           'role[heat-api-cfn]',
                                           'role[heat-api-cloudwatch]'])
        if self.deployment.os_name == "precise":
            # For Ceilometer
            ncmds.extend([
                "apt-get clean",
                "apt-get -y install python-warlock python-novaclient babel"])
            # For Horizon
            ccmds.append(
                "apt-get -y install openstack-dashboard python-django-horizon")
            # For mungerator
            munge.extend(["apt-get -y install python-dev",
                          "apt-get -y install python-setuptools"])
            # For QEMU
            provisioner = str(self.deployment.provisioner)
            if provisioner == "rackspace" or provisioner == "openstack":
                ncmds.extend(
                    ["apt-get update",
                     "apt-get remove qemu-utils -y",
                     "apt-get install qemu-utils -y"])

        if self.deployment.os_name == "centos":
            # For mungerator
            munge.extend(["yum install -y openssl-devel",
                          "yum install -y python-devel",
                          "yum install -y python-setuptools"])

        node_commands = "; ".join(ncmds)
        controller_commands = "; ".join(ccmds)
        for controller in controllers:
            controller.run_cmd(node_commands)
            controller.run_cmd(controller_commands)
        for compute in computes:
            compute.run_cmd(node_commands)

        # backup db
        backup = util.config['upgrade']['commands']['backup-db']
        controller1.run_cmd(backup)

        # Munge away quantum
        munge_dir = "/opt/upgrade/mungerator"
        munge_repo = "https://github.com/rcbops/mungerator"
        munge.extend([
            "rm -rf {0}".format(munge_dir),
            "git clone {0} {1}".format(munge_repo, munge_dir),
            "cd {0}; python setup.py install".format(munge_dir),
            "mungerator munger --client-key /etc/chef-server/admin.pem "
            "--auth-url https://127.0.0.1:443 all-nodes-in-env "
            "--name {0}".format(self.deployment.name)])
        chef_server.run_cmd("; ".join(munge))
        self.deployment.environment.save_locally()

        chef_server.upgrade()
        controller1 = controllers[0]

        # save image upload value
        override = self.deployment.environment.override_attributes
        try:
            image_upload = override['glance']['image_upload']
            override['glance']['image_upload'] = False
            self.deployment.environment.save()
        except KeyError:
            pass

        if self.deployment.feature_in('highavailability'):
            controller2 = controllers[1]
            stop = util.config['upgrade']['commands']['stop-services']
            start = util.config['upgrade']['commands']['start-services']

            # Sleep for vips to move
            controller2.run_cmd(stop)
            sleep(30)

            # Upgrade
            controller1.upgrade()
            controller2.upgrade()

        controller1.upgrade()

        # restore quantum db
        restore_db = util.config['upgrade']['commands']['restore-db']
        controller1.run_cmd(restore_db)

        if self.deployment.feature_in('highavailability'):
            controller1.run_cmd("service haproxy restart; "
                                "monit restart rpcdaemon")
            # restart services of controller2
            controller2.run_cmd(start)

        # restore value of image upload
        if image_upload:
            override['glance']['image_upload'] = image_upload
            self.deployment.environment.save()

        # run the computes
        for compute in computes:
            compute.upgrade(times=2)

        # update packages for neutron on precise
        if self.deployment.feature_in("neutron") and (
                self.deployment.os_name == "precise"):
            cmds = ["apt-get update",
                    "apt-get install python-cmd2 python-pyparsing"]
            cmd = "; ".join(cmds)
            for controller in controllers:
                controller.run_cmd(cmd)
            # for compute in computes:
            #     compute.run_cmd(cmd)
