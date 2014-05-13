import logging

import chef

import monster.deployments.rpcs.deployment as rpcs
import monster.features.node.features as node_features
import monster.orchestrator.base as base
import monster.active

from monster.environments.chef_.environment import Environment

logger = logging.getLogger(__name__)


class Orchestrator(base.Orchestrator):
    def create_deployment_from_file(self, name):
        """Returns a new deployment given a deployment template at path.
        :param name: name for the deployment
        :type name: str
        :rtype: Deployment
        """

        logger.info("Building deployment object for {0}".format(name))

        if chef.Environment(name, api=self.local_api).exists:
            logger.info("Using previous deployment:{0}".format(name))
            return self.load_deployment_from_name(name)

        env = Environment(name=name, local_api=self.local_api,
                          description=name)

        return rpcs.Deployment(name=name, environment=env,
                               status="provisioning")

    def load_deployment_from_name(self, name):
        """Rebuilds a Deployment given a deployment name.
        :param name: name of deployment
        :type name: string
        :rtype: Deployment
        """
        default, override, remote_api = self.load_environment_attributes(name)

        env = Environment(name=name, local_api=self.local_api,
                          remote_api=remote_api, description=name,
                          default_attributes=default,
                          override_attributes=override)

        return rpcs.Deployment(name=name, environment=env,
                               status="loading")

    def load_environment_attributes(self, name):
        local_env = chef.Environment(name, self.local_api)
        chef_auth = local_env.override_attributes.get('remote_chef', None)

        if chef_auth and chef_auth['key']:
            remote_api = node_features.ChefServer.remote_chef_api(chef_auth)
            remove_env = chef.Environment(name, remote_api)
            default = remove_env.default_attributes
            override = remove_env.override_attributes
        else:
            remote_api = None
            default = local_env.default_attributes
            override = local_env.override_attributes

        return default, override, remote_api

    @property
    def local_api(self):
        return chef.autoconfigure()

    def __enter__(self):
        print("In __enter__ !")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            logger.warning("Something went wrong...")
            build_name = monster.active.build_args['name']
            logger.warning("Attempting cleanup!")
            try:
                force_destroy_deployment(build_name)
            except:
                logger.critical("An error occurred during cleanup.")
        else:
            return True


def force_destroy_deployment(build_name):
    import chef
    import monster.database
    for name in monster.active.template.node_names:
        node = chef.Node(name, chef.autoconfigure())
        if node.exists:
            node.delete()
        client = chef.Client(name, chef.autoconfigure())
        if client.exists:
            client.delete()
    env = chef.Environment(build_name, chef.autoconfigure())
    if env.exists:
        env.delete()
    monster.database.remove_key(build_name)

    #delete external servers
    #delete database entries
