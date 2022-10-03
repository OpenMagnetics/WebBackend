import app
import asyncio
import tornado.locks


async def main():
    web = app.Application()
    web.listen(8888)

    shutdown_event = tornado.locks.Event()
    await shutdown_event.wait()


if __name__ == '__main__':
    asyncio.run(main())
