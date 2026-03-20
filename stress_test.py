"""
SnapIntel API Stress Test
Simulates 30 concurrent users hitting the /stories endpoint on production.

Usage:
    pip install aiohttp
    python stress_test.py
"""

import asyncio
import aiohttp
import time
import statistics
import json
import datetime

BASE_URL = "http://wkccwcg0o404wsok0400c8so.91.99.181.1.sslip.io"
ENDPOINT = "/api/v1/user/{username}/stories"
CONCURRENT_USERS = 30

USERNAMES = [
    "realmadrid",
    "nfl",
    "nba",
    "nike",
    "adidas",
    "nasa",
    "psg",
    "espn",
    "spotify",
    "cocacola",
]


async def make_request(session, user_id, username, results):
    """Simulate a single user requesting stories."""
    target_url = BASE_URL + ENDPOINT.format(username=username)
    start = time.monotonic()
    try:
        async with session.get(target_url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            status = resp.status
            body = await resp.read()
            elapsed = (time.monotonic() - start) * 1000  # ms
            try:
                response_json = json.loads(body)
            except Exception:
                response_json = None
            results.append({
                "user_id": user_id,
                "username": username,
                "status": status,
                "time_ms": round(elapsed, 1),
                "size_bytes": len(body),
                "success": status == 200,
                "response": response_json,
            })
            symbol = "\u2705" if status == 200 else "\u274c"
            print(f"  {symbol} User {user_id:>2} | @{username:<16} | {status} | {elapsed:>8.1f}ms | {len(body):>7} bytes")
    except asyncio.TimeoutError:
        elapsed = (time.monotonic() - start) * 1000
        results.append({"user_id": user_id, "username": username, "status": "TIMEOUT", "time_ms": round(elapsed, 1), "size_bytes": 0, "success": False, "response": None})
        print(f"  \u274c User {user_id:>2} | @{username:<16} | TIMEOUT | {elapsed:>8.1f}ms")
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        results.append({"user_id": user_id, "username": username, "status": "ERROR", "time_ms": round(elapsed, 1), "size_bytes": 0, "success": False, "response": None, "error": str(e)})
        print(f"  \u274c User {user_id:>2} | @{username:<16} | ERROR   | {elapsed:>8.1f}ms | {str(e)[:60]}")


async def run_stress_test():
    print("=" * 65)
    print(f"  SnapIntel API Stress Test")
    print(f"  Target:      {BASE_URL + ENDPOINT}")
    print(f"  Concurrent:  {CONCURRENT_USERS} requests across {len(USERNAMES)} usernames")
    print("=" * 65)

    # Health check first
    print("\n[1/3] Health check...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(BASE_URL + "/", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"  \u2705 API is up | instance: {data.get('instance_id', '?')} | proxy: {data.get('proxy_enabled', '?')}")
                else:
                    print(f"  \u274c API returned {resp.status}")
                    return
        except Exception as e:
            print(f"  \u274c Cannot reach API: {e}")
            return

    # Run concurrent requests
    print(f"\n[2/3] Firing {CONCURRENT_USERS} concurrent requests...\n")
    results = []
    overall_start = time.monotonic()

    async with aiohttp.ClientSession() as session:
        tasks = [
            make_request(session, i + 1, USERNAMES[i % len(USERNAMES)], results)
            for i in range(CONCURRENT_USERS)
        ]
        await asyncio.gather(*tasks)

    overall_elapsed = (time.monotonic() - overall_start) * 1000

    # Stats
    print(f"\n[3/3] Results\n")
    print("-" * 65)

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    all_times = [r["time_ms"] for r in results]
    success_times = [r["time_ms"] for r in successful]

    print(f"  Total requests:     {len(results)}")
    print(f"  Successful (200):   {len(successful)}")
    print(f"  Failed:             {len(failed)}")
    print(f"  Success rate:       {len(successful)/len(results)*100:.1f}%")
    print()

    if all_times:
        print(f"  Total wall time:    {overall_elapsed:.0f}ms")
        print(f"  Avg response time:  {statistics.mean(all_times):.1f}ms")
        print(f"  Median:             {statistics.median(all_times):.1f}ms")
        print(f"  Min:                {min(all_times):.1f}ms")
        print(f"  Max:                {max(all_times):.1f}ms")
        if len(all_times) > 1:
            print(f"  Std dev:            {statistics.stdev(all_times):.1f}ms")

    if success_times:
        p95 = sorted(success_times)[int(len(success_times) * 0.95)]
        p99 = sorted(success_times)[int(len(success_times) * 0.99)]
        total_bytes = sum(r["size_bytes"] for r in successful)
        print(f"  P95 latency:        {p95:.1f}ms")
        print(f"  P99 latency:        {p99:.1f}ms")
        print(f"  Total data:         {total_bytes / 1024:.1f} KB")
        print(f"  Throughput:         {len(successful) / (overall_elapsed/1000):.1f} req/s")

    if failed:
        print(f"\n  Failed requests:")
        for r in failed:
            print(f"    User {r['user_id']}: {r['status']} ({r['time_ms']:.0f}ms) {r.get('error', '')}")

    # Save to JSON
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"stress_test_{timestamp}.json"
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "target_url": BASE_URL + ENDPOINT,
        "usernames": USERNAMES,
        "concurrent_users": CONCURRENT_USERS,
        "total_wall_time_ms": round(overall_elapsed, 1),
        "summary": {
            "total_requests": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": f"{len(successful)/len(results)*100:.1f}%",
            "avg_response_ms": round(statistics.mean(all_times), 1) if all_times else 0,
            "median_ms": round(statistics.median(all_times), 1) if all_times else 0,
            "min_ms": round(min(all_times), 1) if all_times else 0,
            "max_ms": round(max(all_times), 1) if all_times else 0,
            "throughput_rps": round(len(successful) / (overall_elapsed / 1000), 1) if overall_elapsed > 0 else 0,
        },
        "requests": results,
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved to: {output_file}")
    print("-" * 65)


if __name__ == "__main__":
    asyncio.run(run_stress_test())
