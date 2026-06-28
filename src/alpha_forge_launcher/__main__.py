"""``alpha-forge`` console_script エントリ。"""
import sys

from alpha_forge_launcher.bootstrap import run


def main() -> None:
    run(sys.argv[1:])


if __name__ == "__main__":
    main()
