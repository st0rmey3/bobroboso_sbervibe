"""Acceptance run through the public API, exactly as an applicant would do it (evidence for Д5, Д7, Д11).

Creates one application, uploads every file of a folder at once WITHOUT saying what each file is
(the type is decided by the model from the content), watches the statuses change and prints a table.

Run on the stand (only needs httpx):
    python backend/scripts/acceptance_run.py case_docs                       # from the host
    docker compose cp case_docs backend:/tmp/case_docs && \
    docker compose exec backend python scripts/acceptance_run.py /tmp/case_docs
Options: --api http://localhost:8000  --country RU
"""

import argparse
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

IN_PROGRESS = {"queued", "preprocessing", "recognizing", "extracting", "validating"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--api", default="http://localhost:8000")
    ap.add_argument("--country", default="RU")
    args = ap.parse_args()
    files = sorted(p for p in Path(args.folder).rglob("*") if p.is_file() and not p.name.startswith("."))
    c = httpx.Client(base_url=args.api, timeout=60)

    created = c.post("/api/public/applications", json={"full_name": "Приёмочный прогон", "country": args.country})
    created.raise_for_status()
    app_id, headers = created.json()["id"], {"X-Application-Token": created.json()["token"]}

    def upload(path: Path) -> tuple[str, int, float, str]:
        t0 = time.monotonic()
        r = c.post(
            f"/api/public/applications/{app_id}/documents",
            headers=headers,
            files={"file": (path.name, path.read_bytes())},
        )
        return path.name, r.status_code, (time.monotonic() - t0) * 1000, r.json().get("detail", "")

    t_start = time.monotonic()
    with ThreadPoolExecutor(8) as pool:
        uploads = list(pool.map(upload, files))
    print(f"Загружено {len(files)} файлов, самый долгий приём {max(u[2] for u in uploads):.0f} мс")
    for name, code, _, detail in uploads:
        if code != 202:
            print(f"  отказ {code}: {name} — {detail}")

    seen: Counter = Counter()
    while True:
        docs = c.get(f"/api/public/applications/{app_id}", headers=headers).json()["documents"]
        states = Counter(d["status"] for d in docs)
        seen.update(s for s in states if s in IN_PROGRESS)
        print(f"  t={time.monotonic() - t_start:5.1f}s {dict(states)}", flush=True)
        if not states.keys() & IN_PROGRESS:
            break
        time.sleep(2)
    total = time.monotonic() - t_start

    print(f"\nВсё разобрано за {total:.1f} с. Промежуточные стадии, которые видели: {sorted(seen)}")
    app = c.get(f"/api/public/applications/{app_id}", headers=headers).json()
    by_id = {d["id"]: d for d in app["documents"]}
    print(f"\n{'Вид документа (по содержимому)':<45} {'Статус':<13} Файл / причина")
    for slot in app["slots"]:
        for doc_id in slot["document_ids"]:
            d = by_id[doc_id]
            print(
                f"{slot['label'][:44]:<45} {d['status']:<13} {d['filename']}"
                + (f" — {d['status_reason']}" if d["status_reason"] else "")
            )
    kinds = [s["label"] for s in app["slots"] if s["doc_type"] != "unknown" and s["document_ids"]]
    print(f"\nВидов документов распознано: {len(kinds)} — {', '.join(kinds)}")
    print(f"Поля по каждому документу — в рабочем месте оператора: заявка «Приёмочный прогон» ({app_id})")


if __name__ == "__main__":
    main()
