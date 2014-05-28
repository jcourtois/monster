import multiprocessing

import monster.orchestrator.chef_.orchestrator as chef_orchestrator

logger = multiprocessing.get_logger()


def get_orchestrator(orchestrator_name):
    if orchestrator_name == "chef":
        return chef_orchestrator.Orchestrator()
    else:
        logger.exception("Orchestrator %s not found." % orchestrator_name)
