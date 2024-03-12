import os
from sentinelhub import SHConfig
from dotenv import load_dotenv


def _load_SH_credentials():
   
    load_dotenv()
   
    sh_client_id = os.environ.get("SENTINELHUB_ID", None)
    if sh_client_id is None:
        print("Error loading SENTINELHUB_ID environmental variable, not found")
        exit()
   
    sh_client_secret = os.environ.get("SENTINELHUB_SECRET", None)
    if sh_client_secret is None:
        print("Error loading SENTINELHUB_SECRET environmental variable, not found")
        exit()

    return sh_client_id, sh_client_secret


def set_SH_credentials()->None:
    config = SHConfig()
    config.sh_client_id, config.sh_client_secret = _load_SH_credentials()
    config.save("default-profile")