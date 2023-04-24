from pathlib import Path


def main():
    Path("/vol/old_renders.dill").touch(exist_ok=True)
    print("it works!")


if __name__ == "__main__":
    main()
