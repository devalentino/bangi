from robyn import Robyn

from src.tracker.routes import router

app = Robyn(__file__)
app.include_router(router)


if __name__ == "__main__":
    app.start()