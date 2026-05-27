"""
Post-deployment smoke test for Cloud Run.
Run: python tests/smoke_test.py [URL]
Exits 0 on pass, 1 on failure — suitable for CI/CD gate.
"""
import sys
import urllib.request
import urllib.error


def check(label: str, url: str, expected_status: int = 200) -> bool:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception as e:
        print(f"  [FAIL] {label}: {e}")
        return False

    ok = status == expected_status
    icon = "[OK]  " if ok else "[FAIL]"
    print(f"  {icon} {label}: HTTP {status}")
    return ok


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else \
        "https://hr-rag-engine-946703664996.asia-south1.run.app"

    url = url.rstrip("/")
    print(f"\nSmoke test → {url}\n")

    results = [
        check("Health endpoint", f"{url}/_stcore/health"),
        check("App root loads",  f"{url}/"),
    ]

    passed = sum(results)
    total  = len(results)
    print(f"\n{passed}/{total} checks passed")

    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
