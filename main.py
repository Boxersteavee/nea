import uvicorn
from api import api

def main():
    uvicorn.run("api:api", host="localhost", port=8085, reload=True)

if __name__ == "__main__":
    main()