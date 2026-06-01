from structlog import getLogger

from oopsys_python import configure, guard, timeit

logger = getLogger("MAIN")


@guard(fallback=None)
@timeit
def compute(expression: str) -> int | None:
    if "+" in expression:
        left, right = expression.split("+")
        return int(left) + int(right)
    if "-" in expression:
        left, right = expression.split("-")
        return int(left) - int(right)
    logger.info("unsupported operation", expression=expression)
    return None


def main() -> None:
    configure()

    expressions = ["2+2", "6-3", "2++2", "a+1", "hello", "crash", "10-4"]
    for expression in expressions:
        result = compute(expression)
        if result is not None:
            logger.info("result", expression=expression, result=result)

    logger.info("done")


if __name__ == "__main__":
    main()
