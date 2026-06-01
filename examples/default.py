def main() -> None:
    while True:
        expression = input("Enter an expression (e.g. 2+2 or 6-3): ")

        # Error:
        # If the user enters an invalid expression such as "2++2",
        # split() will produce unexpected values and the application
        # will crash with ValueError.
        if "+" in expression:
            left, right = expression.split("+")
            result = int(left) + int(right)
            print(f"Result: {result}")

        elif "-" in expression:
            left, right = expression.split("-")
            result = int(left) - int(right)
            print(f"Result: {result}")

        else:
            # Logic limitation:
            # Operations such as "*", "/", "%", etc. are not supported.
            # Examples:
            #   2*2
            #   10/5
            #   hello
            print("Unsupported operation")

        # Error:
        # If the user enters non-numeric values such as:
        #   a+1
        #   hello+world
        # int() will raise ValueError and terminate the application.

        # Critical error:
        # If the user enters:
        #   crash
        # the application will terminate with ZeroDivisionError.
        if expression == "crash":
            print(1 / 0)


if __name__ == "__main__":
    main()
