import uvicorn
from api import api
from config import get_cfg
import subprocess
import os
import shutil

cfg = get_cfg()

# VARIABLES
PORT = int(cfg['api_port'])
USER_DIR = str(cfg['user_data_dir'])
# Functions
def main():

    npm = shutil.which("npm")
    astro_process = subprocess.Popen(
        [npm, "run", "dev"],
        cwd="website"
    )
    os.makedirs(USER_DIR, exist_ok=True)
    uvicorn.run("api:api", host="127.0.0.1", port=PORT, reload=True)

if __name__ == "__main__":
    main()