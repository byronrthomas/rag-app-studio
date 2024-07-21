import csv
import shutil
import os
from urllib.parse import quote
import requests
import json

spider_headers = {
    "Authorization": os.environ["SPIDER_API_KEY"],
    "Content-Type": "application/jsonl",
}


def download_spider_file(url, dest):
    qs = quote(url)
    r = requests.get(
        f"https://api.spider.cloud/data/download?url={qs}",
        headers=spider_headers,
        timeout=60,
    )
    with open(dest, "wb") as f:
        f.write(r.content)


def load_page_data_file(file_path):
    with open(file_path, "r", encoding="UTF-8") as file:
        return json.load(file)


def process_all_page_data(page_data, out_dir):
    processed_dests = {}
    for page in page_data:
        page_path_name = page["pathname"]
        if page_path_name == "/":
            page_path_name = "rootIndex"
        if page_path_name.endswith("/"):
            page_path_name = page_path_name[:-1]

        dest = page_path_name + ".md"
        src = page["url"]
        if dest in processed_dests:
            print(
                f"Duplicate output path name {dest} - from {src} / {page['pathname']} vs {processed_dests[dest]}"
            )
            continue
        processed_dests[dest] = page["pathname"]
        # Check parent folder of dst exists
        if dest.startswith("/"):
            dest = dest[1:]
        file_dest = os.path.join(out_dir, dest)
        os.makedirs(os.path.dirname(file_dest), exist_ok=True)
        print("About to download", src, "to", file_dest)
        download_spider_file(src, file_dest)


def read_csv(file_path):
    result = []
    with open(file_path, "r", encoding="UTF-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            result.append(row)

    return result


def rearrange_files(in_dir, csv_rows, out_dir):
    processed_dests = {}
    for row in csv_rows:
        file_name = row["Filename"]
        path_name = row["PathName"]
        if path_name == "/":
            path_name = "rootIndex"
        if path_name.endswith("/"):
            path_name = path_name[:-1]

        path_name = path_name + ".md"
        src = os.path.join(in_dir, file_name)
        dst = os.path.join(out_dir, file_name)
        if path_name in processed_dests:
            raise ValueError(
                f"Duplicate output path name {path_name} - from {src} / {row['PathName']} vs {processed_dests[path_name]}"
            )
        processed_dests[path_name] = row["PathName"]
        # Check parent folder of dst exists
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        print("About to copy", src, "to", dst)
        # shutil.copy(src, dst)


def detect_common_prefix(f1, f2):
    with open(f1, "r", encoding="UTF-8") as f:
        lines1 = f.readlines()
    with open(f2, "r", encoding="UTF-8") as f:
        lines2 = f.readlines()
    common_line_start = -1
    common_line_end = -1
    for i, (c1, c2) in enumerate(zip(lines1, lines2)):
        if common_line_start == -1:
            if c1 == c2:
                common_line_start = i
                continue
        else:
            if c1 != c2:
                common_line_end = i
                break
    if common_line_start == -1 or common_line_end == -1:
        raise ValueError("No common prefix found")
    print(f"Common prefix from {common_line_start} to {common_line_end}")
    return lines1[common_line_start:common_line_end]


def detect_common_suffix(f1, f2):
    with open(f1, "r", encoding="UTF-8") as f:
        lines1 = f.readlines()
    with open(f2, "r", encoding="UTF-8") as f:
        lines2 = f.readlines()
    common_line_start = -1
    common_line_end = -1
    for i, (c1, c2) in enumerate(zip(reversed(lines1), reversed(lines2))):
        if common_line_start == -1:
            if c1 == c2:
                common_line_start = i
                continue
        else:
            if c1 != c2:
                common_line_end = i
                break
    if common_line_start == -1 or common_line_end == -1:
        raise ValueError("No common suffix found")
    print(f"Common suffix from {common_line_start} to {common_line_end}")
    return lines1[-common_line_end:-common_line_start]


def dedupe_markdown_by_suffix(in_dir, out_dir, suffix_length):
    for root, dirs, files in os.walk(in_dir):
        out_rel = f"{out_dir}/{root[len(in_dir)+1:]}"
        os.makedirs(out_rel, exist_ok=True)
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="UTF-8") as f:
                    lines = f.readlines()
                out_path = os.path.join(out_rel, file)
                print("Processing file", file_path, "writing to", out_path)
                with open(out_path, "w", encoding="UTF-8") as f:
                    f.writelines(lines[0:-suffix_length])

                # raise RuntimeError("Check first file")


def detect_tocs(file_path):
    with open(file_path, "r", encoding="UTF-8") as f:
        lines = f.readlines()
    tocs = []
    toc_start = None
    for i, l in enumerate(lines):
        if toc_start is None:
            if l == "Table of contents\n":
                toc_start = i
        else:
            if l != "\n" and not l.startswith("* "):
                tocs.append((toc_start, i))
                toc_start = None

    if not tocs:
        # raise ValueError(f"Could not find any TOCs in {file_path}")
        print(f"WARN: Could not find any TOCs in {file_path}")
    # print(f"TOCs found at {tocs}")
    return tocs, lines


def dedupe_markdown_by_tocs(in_dir, out_dir):
    for root, dirs, files in os.walk(in_dir):
        out_rel = f"{out_dir}/{root[len(in_dir)+1:]}"
        os.makedirs(out_rel, exist_ok=True)
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                tocs, lines = detect_tocs(file_path)
                out_path = os.path.join(out_rel, file)
                print("Processing file", file_path, "writing to", out_path)
                with open(out_path, "w", encoding="UTF-8") as f:
                    last_toc_end = 0
                    for toc_start, toc_end in tocs:
                        f.writelines(lines[last_toc_end:toc_start])
                        last_toc_end = toc_end
                    f.writelines(lines[last_toc_end:])

                # raise RuntimeError("Check first file")


def dedupe_markdown(in_dir):
    for root, dirs, files in os.walk(in_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="UTF-8") as f:
                    lines = f.readlines()
                startLine = None
                endLine = None
                for line_no, l in enumerate(lines):
                    print(l)
                    if l == "---\n":
                        if startLine is None:
                            startLine = line_no
                    if l.startswith("[Edit this page]") and startLine is not None:
                        endLine = line_no
                        break
                print(f"In {file_path} - startLine: {startLine}, endLine: {endLine}")
                if startLine is None or endLine is None:
                    raise ValueError("Could not find start and end line")
                if startLine < 100 or endLine < len(lines) - 100:
                    raise ValueError("Start or end line too close to beginning or end")

                with open(file_path + ".out", "w", encoding="UTF-8") as f:
                    f.writelines(lines[0:1] + lines[startLine:endLine])

                raise RuntimeError("Check first file")


def dedupe_markdown_by_prefix(in_dir, out_dir, prefix_pattern):
    for root, dirs, files in os.walk(in_dir):
        out_rel = f"{out_dir}/{root[len(in_dir)+1:]}"
        os.makedirs(out_rel, exist_ok=True)
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="UTF-8") as f:
                    lines = f.readlines()
                if lines[1 : 1 + len(prefix_pattern)] != prefix_pattern:
                    print("Skipping file", file_path)
                    continue

                out_path = os.path.join(out_rel, file)
                print("Processing file", file_path, "writing to", out_path)
                with open(out_path, "w", encoding="UTF-8") as f:
                    f.writelines(lines[0:1] + lines[1 + len(prefix_pattern) :])

                # raise RuntimeError("Check first file")
