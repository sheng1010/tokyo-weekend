import json

from sources.mori import fetch_mori_exhibitions
from sources.tobikan import fetch_tobikan_exhibitions
from sources.mot import fetch_mot_exhibitions
from sources.tnm import fetch_tnm_exhibitions
from sources.nact import fetch_nact_exhibitions
from merger.exhibition_merger import merge_exhibitions


def main():
    print("=== start script ===")

    all_events = []

    mori_exhibitions = []
    tobikan_exhibitions = []
    mot_exhibitions = []
    tnm_exhibitions = []
    nact_exhibitions = []

    try:
        print("before mori exhibitions")
        mori_exhibitions = fetch_mori_exhibitions()
        print("after mori exhibitions:", len(mori_exhibitions))
    except Exception as e:
        print("[MORI] failed:", e)

    try:
        print("before tobikan exhibitions")
        tobikan_exhibitions = fetch_tobikan_exhibitions()
        print("after tobikan exhibitions:", len(tobikan_exhibitions))
    except Exception as e:
        print("[TOBIKAN] failed:", e)

    try:
        print("before mot exhibitions")
        mot_exhibitions = fetch_mot_exhibitions()
        print("after mot exhibitions:", len(mot_exhibitions))
    except Exception as e:
        print("[MOT] failed:", e)

    try:
        print("before tnm exhibitions")
        tnm_exhibitions = fetch_tnm_exhibitions()
        print("after tnm exhibitions:", len(tnm_exhibitions))
    except Exception as e:
        print("[TNM] failed:", e)

    try:
        print("before nact exhibitions")
        nact_exhibitions = fetch_nact_exhibitions()
        print("after nact exhibitions:", len(nact_exhibitions))
    except Exception as e:
        print("[NACT] failed:", e)

    merged_exhibitions = merge_exhibitions(
        mori_exhibitions,
        tobikan_exhibitions,
        mot_exhibitions,
        tnm_exhibitions,
        nact_exhibitions,
    )
    all_events.extend(merged_exhibitions)

    print("before write file")
    with open("data/events.json", "w", encoding="utf-8") as f:
        json.dump(all_events, f, ensure_ascii=False, indent=2)
    print("after write file")

    print("events.json updated:", len(all_events))
    print("=== end script ===")


if __name__ == "__main__":
    main()