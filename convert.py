#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Convert domain-list-community to rules."""

from collections import defaultdict
from pathlib import Path


def count_lines(path: Path) -> int:
    """Count lines of a file.

    Args:
        path (Path): file path

    Returns:
        int: number of lines
    """
    with path.open() as fp:
        return len(fp.readlines())


def parse_category(category: Path, rules: list, attrs: dict) -> tuple[list, dict]:
    """Parse category and return clash rules.

    Args:
        category (Path): path of the category
        rules (list): rules of default
        attrs (dict): rules of attrs

    Returns:
        tuple[list, dict]: parsed rules for default and attrs
    """
    with category.open() as f:
        for line in f.readlines():
            if line.startswith("#"):  # skip comments
                continue
            if line.startswith("regexp:"):  # skip regexp rules
                continue
            line = line.split("#")[0].strip()  # strip inline comments
            if "@" in line:
                rule = line.split("@")[0].strip()
                for attr in line.split("@")[1:]:  # parse attrs
                    attrs[attr].append(rule)
                line = rule
            if not line:  # skip empty line
                continue

            if line.startswith("include:"):
                sub_category = line.removeprefix("include:").strip()
                rules, attrs = parse_category(category.with_name(sub_category), rules, attrs)
            else:
                rules.append(line)
    return rules, attrs


def save_metainfo(root: Path, num_header_lines: int = 0) -> None:
    """Save a csv file to display filenames and number of rules.

    Args:
        root (Path): root dir of rules
        num_header_lines (int): number of header lines
    """
    outpath = root / "README.md"
    with open(outpath, "w") as f:
        f.write("| Filename | Rules Count | Attributes |\n")
        f.write("|---|---|---|\n")
        for category in sorted(root.iterdir()):
            filename = category.name
            if filename == "README.md":
                continue
            num_rules = count_lines(category) - num_header_lines
            if "@" in filename:
                filename = filename.replace("@", "@<span></span>")  # add a space to prevent github from parsing it as an email address
                attr = category.stem.split("@")[-1]
                f.write(f"| {filename} | {num_rules} | @{attr} |\n")
            else:
                attr = ""
                f.write(f"| {filename} | {num_rules} | {attr} |\n")


def write_domain_set(outroot: Path, category: str, rules: list, attrs: dict) -> None:
    """Write domain-set rules to file.

    Args:
        outroot (Path): output root dir of rules
        category (str): category name
        rules (list): rules of default
        attrs (dict): rules of attrs
    """

    def save_to_disk(outpath: Path, rule_lst: list) -> None:
        with outpath.open("w") as f:
            for rule in rule_lst:
                if rule.startswith("full:"):
                    f.write(f"{rule.removeprefix('full:')}\n")
                else:
                    f.write(f".{rule}\n")

    outroot.mkdir(parents=True, exist_ok=True)
    outpath = outroot / f"{category}.txt"
    save_to_disk(outpath, rules)
    for attr, rule_list in attrs.items():
        outpath = outroot / f"{category}@{attr}.txt"
        save_to_disk(outpath, rule_list)


def write_rule_set(outroot: Path, category: str, rules: list, attrs: dict) -> None:
    """Write rule-set rules to file.

    Args:
        outroot (Path): output root dir of rules
        category (str): category name
        rules (list): rules of default
        attrs (dict): rules of attrs
    """

    def save_to_disk(outpath: Path, rule_lst: list) -> None:
        with outpath.open("w") as f:
            for rule in rule_lst:
                if rule.startswith("full:"):
                    f.write(f"{rule.replace('full:', 'DOMAIN,')}\n")
                else:
                    f.write(f"DOMAIN-SUFFIX,{rule}\n")

    outroot.mkdir(parents=True, exist_ok=True)
    outpath = outroot / f"{category}.txt"
    save_to_disk(outpath, rules)
    for attr, rule_list in attrs.items():
        outpath = outroot / f"{category}@{attr}.txt"
        save_to_disk(outpath, rule_list)


def main() -> None:
    """Entry point."""
    root = Path("domain-list-community/data")
    domain_set_root = Path("domain-set")
    rule_set_root = Path("rule-set")
    for category in root.iterdir():
        print(category)
        rules = []
        attrs = defaultdict(list)
        rules, attrs = parse_category(category, rules, attrs)
        write_domain_set(domain_set_root, category.name, rules, attrs)
        write_rule_set(rule_set_root, category.name, rules, attrs)
    save_metainfo(domain_set_root)
    save_metainfo(rule_set_root)


if __name__ == "__main__":
    main()
