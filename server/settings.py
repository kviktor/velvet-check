from os import environ


def get_env_variable(name, default=None):
    try:
        return environ[name]
    except KeyError:
        if default is None:
            raise Exception("Set the %s environment variable" % name)
        else:
            return default

MODEL_DEF_PATH = get_env_variable("MODEL_DEF_PATH")
PRETRAINED_MODEL_PATH = get_env_variable("PRETRAINED_MODEL_PATH")

# format: redis://username:password@hostname:port/db_number
BROKER_URL = get_env_variable("BROKER_URL", "redis://localhost:6379/0")
