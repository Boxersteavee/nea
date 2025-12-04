import uvicorn
from api import api
from config import get_cfg, setup
cfg = get_cfg()

# VARIABLES
PORT = int(cfg['api_port'])

# Functions
def main():
    uvicorn.run("api:api", host="localhost", port=PORT, reload=True)

if __name__ == "__main__":
    main()