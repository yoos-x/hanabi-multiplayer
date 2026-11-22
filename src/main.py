from application import Application
from client import HanabiClient

# Run the application
if __name__ == "__main__":
    client = HanabiClient()
    app = Application(client)
    app.run()
