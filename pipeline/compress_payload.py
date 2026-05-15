#!/usr/bin/env python3
"""
Build and verify a zstd-compressed payload for the installation.

The source files are never modified. Text files are copied into a temporary
payload with comments stripped, then archived as a tar file and compressed with
the system `zstd` command. Decompression verification compares the compressed
output against the generated stripped tar payload, not against the source tree.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "dist" / "crookedtimber_payload.tar.zst"
DEFAULT_INCLUDE_PATHS = (ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "app")
EXCLUDED_NAMES = {".DS_Store", "__pycache__"}
EXCLUDED_PAYLOAD_PATHS = {
    "app/static/gemini3pro_cosmic_0_39.json",
    "app/static/lobster-sprite-alpha.png",
    "app/static/starfield-frame.jpg",
}
TEXT_EXTENSIONS = {
    ".cff",
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".svg",
    ".txt",
}


@dataclass(frozen=True)
class PayloadFile:
    source: Path
    archive_name: str
    comment_stripped: bool


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def is_text_payload(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS


def strip_html_comments(text: str) -> str:
    output: list[str] = []
    index = 0
    while index < len(text):
        start = text.find("<!--", index)
        if start < 0:
            output.append(text[index:])
            break
        output.append(text[index:start])
        end = text.find("-->", start + 4)
        if end < 0:
            break
        index = end + 3
    return "".join(output)


def strip_c_like_comments(text: str) -> str:
    """Strip // and /* */ comments while preserving quoted strings."""

    output: list[str] = []
    index = 0
    state = "code"
    quote = ""

    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""

        if state == "code":
            if char in {"'", '"', "`"}:
                quote = char
                state = "string"
                output.append(char)
                index += 1
                continue
            if char == "/" and next_char == "/":
                index += 2
                while index < len(text) and text[index] not in "\r\n":
                    index += 1
                continue
            if char == "/" and next_char == "*":
                index += 2
                while index + 1 < len(text) and not (
                    text[index] == "*" and text[index + 1] == "/"
                ):
                    index += 1
                index += 2 if index + 1 < len(text) else 0
                continue
            output.append(char)
            index += 1
            continue

        if state == "string":
            output.append(char)
            if char == "\\":
                if index + 1 < len(text):
                    output.append(text[index + 1])
                    index += 2
                    continue
            elif char == quote:
                state = "code"
            index += 1
            continue

    return "".join(output)


def strip_shader_template_comments(text: str) -> str:
    pattern = re.compile(
        r"((?:const|let|var)\s+[A-Za-z_$][\w$]*Shader[A-Za-z0-9_$]*\s*=\s*`)(.*?)(`;)",
        re.DOTALL,
    )

    def replace(match: re.Match[str]) -> str:
        prefix, body, suffix = match.groups()
        return f"{prefix}{strip_c_like_comments(body)}{suffix}"

    return pattern.sub(replace, text)


def strip_comments_for_payload(path: Path, text: str) -> str:
    suffix = path.suffix.lower()
    if suffix in {".html", ".md", ".svg"}:
        text = strip_html_comments(text)
    if suffix in {".css", ".html", ".js", ".mjs", ".svg"}:
        text = strip_c_like_comments(text)
    if suffix in {".js", ".mjs"}:
        text = strip_shader_template_comments(text)
    return text


def iter_payload_files(include_paths: tuple[Path, ...], strip_comments: bool) -> list[PayloadFile]:
    files: list[PayloadFile] = []
    for include_path in include_paths:
        if include_path.is_file():
            relative = include_path.relative_to(ROOT).as_posix()
            files.append(
                PayloadFile(
                    source=include_path,
                    archive_name=relative,
                    comment_stripped=strip_comments and is_text_payload(include_path),
                )
            )
            continue

        if include_path.is_dir():
            for path in sorted(include_path.rglob("*")):
                if path.name in EXCLUDED_NAMES or any(part in EXCLUDED_NAMES for part in path.parts):
                    continue
                if path.is_file():
                    relative = path.relative_to(ROOT).as_posix()
                    if relative in EXCLUDED_PAYLOAD_PATHS:
                        continue
                    files.append(
                        PayloadFile(
                            source=path,
                            archive_name=relative,
                            comment_stripped=strip_comments and is_text_payload(path),
                        )
                    )
            continue

        raise FileNotFoundError(include_path)

    return sorted(files, key=lambda item: item.archive_name)


def write_payload_tar(payload_files: list[PayloadFile], tar_path: Path) -> dict[str, str]:
    staged_hashes: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="ct-payload-") as tmp:
        stage = Path(tmp)
        for payload_file in payload_files:
            staged_path = stage / payload_file.archive_name
            staged_path.parent.mkdir(parents=True, exist_ok=True)
            if payload_file.comment_stripped:
                text = strip_comments_for_payload(payload_file.source, read_text(payload_file.source))
                staged_path.write_text(text, encoding="utf-8")
            else:
                shutil.copyfile(payload_file.source, staged_path)
            staged_hashes[payload_file.archive_name] = sha256_file(staged_path)

        with tarfile.open(tar_path, "w") as tar:
            for payload_file in payload_files:
                staged_path = stage / payload_file.archive_name
                tar_info = tar.gettarinfo(staged_path, arcname=payload_file.archive_name)
                tar_info.uid = 0
                tar_info.gid = 0
                tar_info.uname = ""
                tar_info.gname = ""
                tar_info.mtime = 0
                with staged_path.open("rb") as handle:
                    tar.addfile(tar_info, handle)

    return staged_hashes


def compress_with_zstd(
    tar_path: Path,
    output_path: Path,
    level: int,
    long_window_log: int | None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = ["zstd"]
    if level > 19:
        command.append("--ultra")
    command.append(f"-{level}")
    if long_window_log is not None:
        command.append(f"--long={long_window_log}")
    command.extend(
        [
            "--force",
            "--quiet",
            "-o",
            str(output_path),
            str(tar_path),
        ]
    )
    subprocess.run(
        command,
        check=True,
    )


def decompress_with_zstd(input_path: Path, output_tar_path: Path) -> None:
    subprocess.run(
        [
            "zstd",
            "--decompress",
            "--force",
            "--quiet",
            "-o",
            str(output_tar_path),
            str(input_path),
        ],
        check=True,
    )


def safe_extract_tar(tar_path: Path, extract_dir: Path) -> None:
    with tarfile.open(tar_path, "r") as tar:
        for member in tar.getmembers():
            member_path = Path(member.name)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError(f"Unsafe tar member: {member.name}")
        tar.extractall(extract_dir, filter="data")


def assert_extract_target_is_safe(extract_dir: Path) -> None:
    if extract_dir.exists() and any(extract_dir.iterdir()):
        raise FileExistsError(f"Refusing to extract into non-empty directory: {extract_dir}")
    extract_dir.mkdir(parents=True, exist_ok=True)


def verify_tar_contents(tar_path: Path, expected_hashes: dict[str, str]) -> None:
    actual_hashes: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="ct-verify-") as tmp:
        extract_dir = Path(tmp)
        safe_extract_tar(tar_path, extract_dir)

        for path in sorted(extract_dir.rglob("*")):
            if path.is_file():
                archive_name = path.relative_to(extract_dir).as_posix()
                actual_hashes[archive_name] = sha256_file(path)

    if actual_hashes != expected_hashes:
        missing = sorted(set(expected_hashes) - set(actual_hashes))
        extra = sorted(set(actual_hashes) - set(expected_hashes))
        changed = sorted(
            name
            for name in set(expected_hashes) & set(actual_hashes)
            if expected_hashes[name] != actual_hashes[name]
        )
        raise RuntimeError(
            "Decompressed payload verification failed: "
            f"missing={missing}, extra={extra}, changed={changed}"
        )


def format_size(byte_count: int) -> str:
    units = ("B", "KiB", "MiB", "GiB")
    size = float(byte_count)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{byte_count} B"
        size /= 1024
    return f"{byte_count} B"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create and verify a zstd-compressed README/AGENTS/app payload."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Compressed output path. Default: {DEFAULT_OUTPUT.relative_to(ROOT)}",
    )
    parser.add_argument(
        "--level",
        type=int,
        default=19,
        help="zstd compression level. Default: 19",
    )
    parser.add_argument(
        "--keep-comments",
        action="store_true",
        help="Keep comments in text/code payload files instead of stripping them.",
    )
    parser.add_argument(
        "--long-window-log",
        type=int,
        help="Pass --long=N to zstd for a larger match window.",
    )
    parser.add_argument(
        "--decompress",
        type=Path,
        help="Decompress an existing .zst payload instead of building a new one.",
    )
    parser.add_argument(
        "--extract-to",
        type=Path,
        help="Extract the decompressed tar payload to this empty directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.decompress and not args.extract_to:
        raise SystemExit("--decompress requires --extract-to")

    if args.decompress:
        input_path = args.decompress if args.decompress.is_absolute() else ROOT / args.decompress
        extract_dir = args.extract_to if args.extract_to.is_absolute() else ROOT / args.extract_to
        assert_extract_target_is_safe(extract_dir)
        with tempfile.TemporaryDirectory(prefix="ct-zstd-extract-") as tmp:
            tar_path = Path(tmp) / "crookedtimber_payload.tar"
            decompress_with_zstd(input_path, tar_path)
            safe_extract_tar(tar_path, extract_dir)
        print(f"input: {input_path.relative_to(ROOT) if input_path.is_relative_to(ROOT) else input_path}")
        print(f"extracted to: {extract_dir.relative_to(ROOT) if extract_dir.is_relative_to(ROOT) else extract_dir}")
        print("decompression: ok")
        return 0

    output_path = args.output if args.output.is_absolute() else ROOT / args.output
    strip_comments = not args.keep_comments
    payload_files = iter_payload_files(DEFAULT_INCLUDE_PATHS, strip_comments)

    with tempfile.TemporaryDirectory(prefix="ct-zstd-") as tmp:
        tmp_dir = Path(tmp)
        tar_path = tmp_dir / "crookedtimber_payload.tar"
        decompressed_tar_path = tmp_dir / "crookedtimber_payload.verify.tar"

        staged_hashes = write_payload_tar(payload_files, tar_path)
        uncompressed_size = tar_path.stat().st_size
        compress_with_zstd(tar_path, output_path, args.level, args.long_window_log)
        decompress_with_zstd(output_path, decompressed_tar_path)

        if sha256_file(tar_path) != sha256_file(decompressed_tar_path):
            raise RuntimeError("Decompressed tar hash does not match generated tar payload")
        verify_tar_contents(decompressed_tar_path, staged_hashes)
        if args.extract_to:
            extract_dir = args.extract_to if args.extract_to.is_absolute() else ROOT / args.extract_to
            assert_extract_target_is_safe(extract_dir)
            safe_extract_tar(decompressed_tar_path, extract_dir)

    stripped_count = sum(1 for payload_file in payload_files if payload_file.comment_stripped)
    output_size = output_path.stat().st_size
    print(f"payload files: {len(payload_files)}")
    print(f"comments: {'kept' if args.keep_comments else 'stripped'}")
    print(f"comment-stripped text files: {stripped_count}")
    print(f"zstd level: {args.level}")
    print(f"zstd long window: {args.long_window_log if args.long_window_log is not None else 'default'}")
    print(f"uncompressed payload tar: {uncompressed_size} bytes ({format_size(uncompressed_size)})")
    print(f"compressed zstd: {output_size} bytes ({format_size(output_size)})")
    print(f"output: {output_path.relative_to(ROOT)}")
    print("verification: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
