#!/usr/bin/env python
"""
Monitor specified .out files in a directory and display the last few lines of the latest file for each type.

This script watches a directory for output files (e.g., "flow" or "refine") created during the adaptation process
and updates the terminal with the most recent output lines.
"""
import os
import time
import sys
import argparse


def get_latest_out_files(output_dir, prefixes):
    latest_files = {}
    for prefix in prefixes:
        files = sorted([f for f in os.listdir(output_dir) if f.startswith(prefix) and f.endswith(".out")])
        latest_files[prefix] = files[-1] if files else None
    return latest_files


def tail_file(filepath, lines=15):
    with open(filepath, "r") as file:
        data = file.readlines()
    return "".join(data[-lines:])


def tracking_loop(output_dir, num_tail_lines, prefixes):
    last_files = {prefix: None for prefix in prefixes}
    last_sizes = {prefix: 0 for prefix in prefixes}
    last_contents = {prefix: "" for prefix in prefixes}

    try:
        while True:
            latest_files = get_latest_out_files(output_dir, prefixes)

            for prefix in prefixes:
                latest_file = latest_files[prefix]
                if latest_file:
                    latest_path = os.path.join(output_dir, latest_file)
                    file_size = os.path.getsize(latest_path)
                    if latest_file != last_files[prefix] or file_size > last_sizes[prefix]:
                        last_contents[prefix] = tail_file(latest_path, lines=num_tail_lines)
                        last_files[prefix], last_sizes[prefix] = latest_file, file_size

            sys.stdout.write("\033[H\033[J")  # Clear the screen (ANSI escape code)
            for prefix in prefixes:
                print(f"=== Latest {prefix.capitalize()} File: {last_files[prefix]} ===")
                print(last_contents[prefix])
                print()

            sys.stdout.flush()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Monitoring stopped.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-d", "--directory", type=str, default="./Flow", help="Directory containing .out files.")
    parser.add_argument("-n", "--num_lines", type=int, default=15, help="Number of lines to tail for each file.")
    parser.add_argument(
        "-p", "--prefixes", nargs="+", default=["flow", "refine"], help="Prefixes of file types to monitor."
    )
    args = parser.parse_args()
    tracking_loop(args.directory, args.num_lines, args.prefixes)


if __name__ == "__main__":
    main()
