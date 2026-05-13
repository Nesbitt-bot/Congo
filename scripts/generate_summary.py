#!/usr/bin/env python3
from build_site import read_catalog, write_summary_files


def main() -> None:
    catalog = read_catalog()
    write_summary_files(catalog)
    print("Generated summary indexes and per-category markdown files under summary/")


if __name__ == "__main__":
    main()
