import asyncio

from structlog import getLogger

from oopsys_python import configure, guard, ignore, install

logger = getLogger("MAIN")


@guard(fallback=None)
async def divide(a: int, b: int) -> float:
    await asyncio.sleep(0)
    return a / b


@ignore
async def must_not_be_touched() -> None:
    raise RuntimeError("intentional")


async def main() -> None:
    configure()
    install()

    logger.info("ok", result=await divide(10, 2))
    logger.info("safe", result=await divide(10, 0))

    try:
        await must_not_be_touched()
    except RuntimeError:
        logger.info("ignore works")

    logger.info("done")


if __name__ == "__main__":
    asyncio.run(main())
