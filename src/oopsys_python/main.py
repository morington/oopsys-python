import asyncio
from contextlib import asynccontextmanager

from structlog import getLogger

from oopsys_python.configuration import Configuration, Loggers

logger = getLogger(Loggers.main.name)


async def main() -> None:
    configuration = Configuration()

    Loggers(developer_mode=configuration.is_development)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Application interrupted by user")
