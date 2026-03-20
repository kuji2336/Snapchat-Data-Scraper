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

BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/v1/user/realmadrid/stories"
CONCURRENT_USERS = 30
TARGET_URL = BASE_URL + ENDPOINT


async def make_request(session, user_id, results):
    """Simulate a single user requesting stories."""
    start = time.monotonic()
    try:
        async with session.get(TARGET_URL, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            status = resp.status
            body = await resp.read()
            elapsed = (time.monotonic() - start) * 1000  # ms
            results.append({
                "user_id": user_id,
                "status": status,
                "time_ms": round(elapsed, 1),
                "size_bytes": len(body),
                "success": status == 200,
            })
            symbol = "\u2705" if status == 200 else "\u274c"
            print(f"  {symbol} User {user_id:>2} | {status} | {elapsed:>8.1f}ms | {len(body):>7} bytes")
    except asyncio.TimeoutError:
        elapsed = (time.monotonic() - start) * 1000
        results.append({"user_id": user_id, "status": "TIMEOUT", "time_ms": round(elapsed, 1), "size_bytes": 0, "success": False})
        print(f"  \u274c User {user_id:>2} | TIMEOUT | {elapsed:>8.1f}ms")
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        results.append({"user_id": user_id, "status": "ERROR", "time_ms": round(elapsed, 1), "size_bytes": 0, "success": False, "error": str(e)})
        print(f"  \u274c User {user_id:>2} | ERROR   | {elapsed:>8.1f}ms | {str(e)[:60]}")


async def run_stress_test():
    print("=" * 65)
    print(f"  SnapIntel API Stress Test")
    print(f"  Target:      {TARGET_URL}")
    print(f"  Concurrent:  {CONCURRENT_USERS} users")
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
        tasks = [make_request(session, i + 1, results) for i in range(CONCURRENT_USERS)]
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

    print("-" * 65)


if __name__ == "__main__":
    asyncio.run(run_stress_test())
