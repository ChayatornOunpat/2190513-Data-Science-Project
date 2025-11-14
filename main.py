import os
import json
import pandas as pd
import asyncio
import aiofiles
from tqdm.asyncio import tqdm_asyncio


def normalize_entry(entry):
    """Normalize a Scopus Abstract Retrieval JSON entry."""

    def get_path(d, path, default=None):
        curr = d
        for p in path.split('.'):
            if isinstance(curr, dict) and p in curr:
                curr = curr[p]
            else:
                return default
        return curr

    out = {
        "eid": get_path(entry, "coredata.eid") or get_path(entry, "eid"),
        "title": get_path(entry, "coredata.dc:title") or get_path(entry, "dc:title") or get_path(entry, "title"),
        "abstract": get_path(entry, "coredata.dc:description") or get_path(entry, "dc:description") or get_path(entry,
                                                                                                                "abstract"),
        "doi": get_path(entry, "coredata.prism:doi") or get_path(entry, "prism:doi") or get_path(entry, "doi"),
        "publication_name": get_path(entry, "coredata.prism:publicationName") or get_path(entry,
                                                                                          "prism:publicationName"),
        "cover_date": get_path(entry, "coredata.prism:coverDate") or get_path(entry, "prism:coverDate"),
        "citedby_count": get_path(entry, "coredata.citedby-count") or get_path(entry, "citedby-count") or 0,
    }

    # ------------------------------
    # Authors
    # ------------------------------
    author_ids = []
    authors = (
            get_path(entry, "authors.author")
            or get_path(entry, "authors")
            or get_path(entry, "author")
            or []
    )
    if isinstance(authors, dict) and "author" in authors:
        authors = authors["author"]

    if isinstance(authors, list):
        for a in authors:
            if isinstance(a, dict):
                aid = (a.get("@auid") or a.get("authid")
                       or a.get("authorId") or a.get("id"))
                if aid:
                    author_ids.append(aid)

    out["author_ids"] = author_ids

    # ------------------------------
    # Subject Areas
    # ------------------------------
    subject_areas = []
    subj = get_path(entry, "subject-areas.subject-area") or get_path(entry, "subject_areas")

    if isinstance(subj, list):
        for s in subj:
            if isinstance(s, dict):
                name = s.get("$") or s.get("name") or s.get("@abbrev")
                if name:
                    subject_areas.append(name)

    out["subject_areas"] = subject_areas

    # ------------------------------
    # Affiliations
    # ------------------------------
    affs_out = []
    aff = get_path(entry, "affiliation") or get_path(entry, "affiliations")

    if isinstance(aff, dict) and "affiliation" in aff:
        aff = aff["affiliation"]

    if isinstance(aff, list):
        for a in aff:
            if isinstance(a, dict):
                affs_out.append({
                    "afid": a.get("@afid") or a.get("afid") or a.get("id"),
                    "name": a.get("affilname") or a.get("name"),
                    "country": a.get("affiliation-country") or a.get("country"),
                })

    out["affiliations"] = affs_out

    return out

async def load_single_json(file_path):
    """Asynchronously read and parse one JSON file."""
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()
        raw = json.loads(content)

        # Detect record list (same logic as before)
        if isinstance(raw, dict):
            if "abstracts-retrieval-response" in raw:
                records = [raw["abstracts-retrieval-response"]]
            elif "search-results" in raw and "entry" in raw["search-results"]:
                records = raw["search-results"]["entry"]
            else:
                list_fields = [
                    k for k, v in raw.items()
                    if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict)
                ]
                records = raw[list_fields[0]] if list_fields else [raw]

        elif isinstance(raw, list):
            records = raw
        else:
            records = [raw]

        return [normalize_entry(r) for r in records]
    except Exception as e:
        print(f"[ERROR] Failed to load {file_path}: {e}")
        return []


async def load_scopus_directory_async(dir_path):
    files = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.lower().endswith(".json")]

    results = []
    sem = asyncio.Semaphore(100)  # limit concurrency to avoid I/O overload

    async def sem_task(f):
        async with sem:
            return await load_single_json(f)

    for chunk in tqdm_asyncio.as_completed([sem_task(f) for f in files], desc="Loading JSON (async)"):
        records = await chunk
        results.extend(records)

    return pd.DataFrame(results)


if __name__ == "__main__":
    df = asyncio.run(load_scopus_directory_async(
        r"C:\Users\ASUS\Downloads\ScopusData2018-2023\ScopusData2018-2023\all"
    ))
    df.to_csv("data.csv", index=False)

