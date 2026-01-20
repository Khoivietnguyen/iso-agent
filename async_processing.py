import os
import asyncio
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


INPUT_ROOT_DIR = "tmp"
OUTPUT_ROOT_DIR = "out_dir"
API_KEY = os.environ.get('API_KEY')
BASE_URL = "https://extraction-api.nanonets.com/api/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

MAX_CONCURRENT_BATCHES = 5
POLL_INTERVAL_SECONDS = 5
POLL_TIMEOUT_SECONDS = 300
REQUEST_TIMEOUT_SECONDS = 120


def list_directories(path: str = ".") -> List[str]:
    """List directories recursively under the given path."""
    directories: List[str] = []
    for dirpath, dirnames, _ in os.walk(path):
        for dirname in dirnames:
            directories.append(os.path.join(dirpath, dirname))
    return directories


def send_files(directory: Path) -> Optional[Dict[str, Any]]:
    """Submit pending PDF files in a directory for asynchronous extraction."""
    files_list = list(directory.glob("*.pdf"))
    relative_path = directory.relative_to(Path(INPUT_ROOT_DIR))
    output_path = Path(OUTPUT_ROOT_DIR) / relative_path
    output_path.mkdir(parents=True, exist_ok=True)

    pending_files: List[Path] = []
    for input_file in files_list:
        out_file = input_file.stem + ".md"
        target_file = output_path / out_file
        if target_file.exists():
            print(f"Skipping file: {input_file}")
            continue
        print(f"Queueing {input_file}")
        pending_files.append(input_file)

    if not pending_files:
        return None

    try:
        with ExitStack() as stack:
            files_to_upload = [
                ("files", stack.enter_context(open(file_path, "rb")))
                for file_path in pending_files
            ]
            response = requests.post(
                f"{BASE_URL}/extract/batch",
                headers=HEADERS,
                files=files_to_upload,
                data={"output_format": "markdown"},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            result = response.json()
            print(f"Submitted {len(pending_files)} file(s) from {directory}")
            return {"out_path": output_path, "result": result}
    except requests.RequestException as exc:
        print(f"Failed to submit batch for {directory}: {exc}")
    except ValueError as exc:
        print(f"Could not decode response for {directory}: {exc}")

    return None


def poll_result(
    record_id: str,
    max_wait: int = POLL_TIMEOUT_SECONDS,
    interval: int = POLL_INTERVAL_SECONDS,
) -> Dict[str, Any]:
    """Poll the extraction result for a record until it completes."""
    start = time.time()
    while time.time() - start < max_wait:
        try:
            response = requests.get(
                f"{BASE_URL}/extract/results/{record_id}",
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            result = response.json()
        except requests.RequestException as exc:
            print(f"Polling record {record_id} failed: {exc}")
            time.sleep(interval)
            continue

        status = result.get("status")
        if status == "completed":
            return result
        if status == "failed":
            raise RuntimeError(
                f"Extraction failed for {record_id}: {result.get('message')}"
            )

        time.sleep(interval)

    raise TimeoutError(f"Extraction timed out for {record_id}")


def extract_markdown_content(payload: Dict[str, Any]) -> str:
    """Extract markdown content from the poll response."""
    try:
        return payload["result"]["markdown"]["content"]
    except KeyError as exc:
        raise KeyError("Markdown content missing in poll result") from exc


async def poll_and_save_record(record: Dict[str, Any], output_dir: Path) -> Optional[Path]:
    """Wait for a record to finish processing, then persist its markdown output."""
    record_id = record.get("record_id")
    if not record_id:
        print("Skipping record without record_id")
        return None

    filename = record.get("filename") or f"{record_id}.md"
    output_filename = Path(filename).with_suffix(".md").name
    print(f"Waiting for record {record_id}...")

    try:
        poll_payload = await asyncio.to_thread(
            poll_result,
            record_id,
            POLL_TIMEOUT_SECONDS,
            POLL_INTERVAL_SECONDS,
        )
        markdown = extract_markdown_content(poll_payload)
    except Exception as exc:
        print(f"Record {record_id} failed: {exc}")
        return None

    destination = output_dir / output_filename
    destination.write_text(markdown, encoding="utf-8")
    print(f"Saved {destination}")
    return destination


async def process_directory(directory: Path, semaphore: asyncio.Semaphore) -> str:
    """Submit files in a directory and persist their extraction outputs."""
    async with semaphore:
        submission = await asyncio.to_thread(send_files, directory)

    if not submission:
        return "No Content"

    result_payload = submission.get("result") or {}
    if not result_payload.get("success"):
        print(f"Batch request failed for {directory}: {result_payload}")
        return "Failed"

    records = [
        record for record in result_payload.get("records", []) if record.get("success")
    ]
    if not records:
        print(f"No successful records for {directory}")
        return "No Successful Records"

    await asyncio.gather(
        *(poll_and_save_record(record, submission["out_path"]) for record in records)
    )
    return "OK"


async def main(directories: List[str]) -> List[str]:
    """Process every directory concurrently."""
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_BATCHES)
    tasks = [process_directory(Path(d), semaphore) for d in directories]
    return await asyncio.gather(*tasks)


if __name__ == "__main__":
    directories = list_directories(path=INPUT_ROOT_DIR)
    asyncio.run(main(directories))
