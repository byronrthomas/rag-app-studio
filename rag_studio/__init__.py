import logging
import os
import sys

lvl = logging.getLevelName(os.environ.get("LOG_LEVEL", "DEBUG"))
logging.basicConfig(stream=sys.stdout, level=lvl)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))
