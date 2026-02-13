import uvicorn
from config import get_cfg
import subprocess
import os
import shutil

# Set variables from config
cfg = get_cfg()
PORT = int(cfg['api_port'])
USER_DIR = str(cfg['user_data_dir'])
HOST_IP = cfg['host_ip']

# Main function
def main():

    # Run website server
    npm = shutil.which("npm")
    astro_process = subprocess.Popen(
        [npm, "run", "dev"],
        cwd="website"
    )
    os.makedirs(USER_DIR, exist_ok=True)
    # Run the API on localhost on the configured configured port
    uvicorn.run("api:api", host=HOST_IP, port=PORT, reload=True)

if __name__ == "__main__":
    main()