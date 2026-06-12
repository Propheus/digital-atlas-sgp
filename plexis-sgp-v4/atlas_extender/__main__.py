"""CLI: python -m atlas_extender 'use case text'"""
import sys
from .pipeline import extend


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m atlas_extender 'natural language use case'")
        print("Example: python -m atlas_extender 'Where should we open a new specialty café in Singapore?'")
        sys.exit(1)
    extend(" ".join(sys.argv[1:]))


if __name__ == "__main__":
    main()
