#################################################
# config.py
#
# getConfig: return value set by configuration 
#            which can be from config map or environment variable
#            if not provided, return default value
# getPath:   return path relative to mount path
#            create new if not exists
#            mount path is set by configuration
#            if mount path cannot be write, 
#            set to local folder (/server)
#
#################################################

import os

# must be writable (for shared volume mount)
MNT_PATH = "/mnt"
# can be read only (for configmap mount)
CONFIG_PATH = "/etc/config"

modelItemNameMap = {
    "Abs": "NODE_TOTAL",
    "AbsComponent": "NODE_COMPOENTS",
    "Dyn": "POD_TOTAL",
    "DynComponent": "POD_COMPONENTS"
}

modelTypeNameMap = {
    "Power": "POWER",
    "ModelWeight": "MODEL_WEIGHT"
}

modelEnvMap = {"{}{}".format(modelItemKey, modelTypeKey): "{}_{}".format(modelItemValue, modelTypeValue) for modelItemKey, modelItemValue in modelItemNameMap.items() for modelTypeKey, modelTypeValue in modelTypeNameMap.items() }
estimatorKeyMap = {"{}Power".format(modelItemKey): "{}_ESTIMATOR".format(modelItemNameMap[modelItemKey]) for modelItemKey in modelItemNameMap.keys()}
initUrlKeyMap = {"{}Power".format(modelItemKey): "{}_INIT_URL".format(modelItemNameMap[modelItemKey]) for modelItemKey in modelItemNameMap.keys()}

def getConfig(key, default):
    # check configmap path
    file = os.path.join(CONFIG_PATH, key)
    if os.path.exists(file):
        with open(file, "r") as f:
            return f.read()
    # check env
    return os.getenv(key, default)

def getInitModel(output_type):
    if output_type in estimatorKeyMap:
        enabled = getConfig(estimatorKeyMap[output_type], "false").lower() == "true"
        if enabled:
            return getConfig(initUrlKeyMap[output_type], "")
        else:
            print("{} is not enaled".format(output_type))
    return ""

def getPath(subpath):
    path = os.path.join(MNT_PATH, subpath)
    if not os.path.exists(path):
        os.mkdir(path)
    return path

# update value from environment if exists
MNT_PATH = getConfig('MNT_PATH', MNT_PATH)
if not os.path.exists(MNT_PATH) or not os.access(MNT_PATH, os.W_OK):
    # use local path if not exists or cannot write
    MNT_PATH = os.path.join(os.path.dirname(__file__), '..')
print("mount path: ", MNT_PATH)

CONFIG_PATH = getConfig('CONFIG_PATH', CONFIG_PATH)

def set_env_from_model_config():
    model_config = getConfig('MODEL_CONFIG', "")
    if model_config != "":
        lines = model_config.splitlines()
        for line in lines:
            splits = line.split('=')
            if len(splits) > 1:
                os.environ[splits[0]] = splits[1]
                print("set {} to {}.".format(splits[0], splits[1]))