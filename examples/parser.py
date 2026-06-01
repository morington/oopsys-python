import asyncio

import httpx
from structlog import getLogger

from oopsys_python import configure, guard, timeit

logger = getLogger("MAIN")


@guard(fallback=None)
@timeit
async def fetch_fact() -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get("https://catfact.ninja/fact")
        response.raise_for_status()
        return str(response.json()["fact"])


async def main() -> None:
    configure()

    while True:
        fact = await fetch_fact()
        if fact is None:
            await asyncio.sleep(5)
            continue

        logger.info("cat fact", fact=fact)
        await asyncio.sleep(15)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("stopped by user")
