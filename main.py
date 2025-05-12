import asyncio

from application import Application

if __name__ == "__main__":
    app = Application()
    asyncio.run(app.run())
