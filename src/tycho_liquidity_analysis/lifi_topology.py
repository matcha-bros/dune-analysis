import json
import os
import sys
from dataclasses import dataclass
from decimal import Decimal, getcontext
from pathlib import Path

import requests

from tycho_liquidity_analysis.config import REPO_ROOT, Settings


getcontext().prec = 80

CHAIN_ID = "1"
LIFI_QUOTE_URL = "https://li.quest/v1/quote"
LIFI_DIAMOND = "0x1231DEB6f5749EF6cE6943a275A1D3E7486F4EaE"
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

DEFAULT_SENDER = "0x28C6c06298d514Db089934071355E5743bf21d60"

TOKENS = {
    USDC.lower(): ("USDC", 6),
    WETH.lower(): ("WETH", 18),
    "0xdac17f958d2ee523a2206206994597c13d831ec7".lower(): ("USDT", 6),
    "0x6b175474e89094c44da98b954eedeac495271d0f".lower(): ("DAI", 18),
}

KNOWN_CONTRACTS = {
    LIFI_DIAMOND.lower(): "LI.FI Diamond",
    "0x685527c551cc40ce1f1c9818cd8683307076e4ed".lower(): "LI.FI FeeCollector",
    "0x6131b5fae19ea4f9d964eac0408e4408b66337b5".lower(): "Kyber MetaAggregationRouterV2",
    "0x617dee16b86534a5d792a4d7a62fb491b544111e".lower(): "Kyber Executor",
    "0xe3d41d19564922c9952f692c5dd0563030f5f2ef".lower(): "Native CreditVault",
    "0xa540ec8c73322200d68e1b86c471a5c850854f22".lower(): "NativeRouter V3",
    "0xa929c559e5e6537359680f39cb4e3708e1a14dd1".lower(): "Nordstern",
    "0xf2614a233c7c3e7f08b1f887ba133a13f1eb2c55".lower(): "Sushi RouteProcessor",
    "0xe0554a476a092703abdB3Ef35c80e0D76d32939F".lower(): "Uniswap V3 USDC/WETH 0.01%",
    "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640".lower(): "Uniswap V3 USDC/WETH 0.05%",
}


@dataclass(frozen=True)
class TopologyArgs:
    from_token: str = USDC
    to_token: str = WETH
    amount: int = 1_000_000_000
    sender: str = DEFAULT_SENDER
    slippage: str = "0.005"
    gas: int = 8_000_000
    save_prefix: str = ""


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_default_env_files() -> None:
    settings = Settings()
    load_env_file(REPO_ROOT / ".env")
    load_env_file(settings.tycho_simulation_dir / ".env")


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing required env var {name}")
    return value


def address_topic(address: str) -> str:
    return "0x" + "0" * 24 + address.lower().removeprefix("0x")


def encode_approve(spender: str, amount: int) -> str:
    selector = "095ea7b3"
    spender_word = spender.lower().removeprefix("0x").rjust(64, "0")
    amount_word = hex(amount)[2:].rjust(64, "0")
    return "0x" + selector + spender_word + amount_word


def normalize_address(value: str) -> str:
    if not value:
        return value
    value = value.lower()
    if value.startswith("0x") and len(value) == 66:
        return "0x" + value[-40:]
    return value


def label(address: str, sender: str) -> str:
    if not address:
        return ""
    lower = address.lower()
    if lower == sender.lower():
        return "Sender"
    known = KNOWN_CONTRACTS.get(lower)
    if known:
        return known
    token = TOKENS.get(lower)
    if token:
        return token[0]
    return address


def token_amount(token: str, raw: int) -> str:
    symbol, decimals = TOKENS.get(token.lower(), ("UNKNOWN", 18))
    amount = Decimal(raw) / (Decimal(10) ** decimals)
    text = format(amount.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return f"{text} {symbol}"


def fetch_lifi_quote(args) -> dict:
    params = {
        "fromChain": CHAIN_ID,
        "toChain": CHAIN_ID,
        "fromToken": args.from_token,
        "toToken": args.to_token,
        "fromAmount": str(args.amount),
        "fromAddress": args.sender,
        "slippage": str(args.slippage),
    }
    response = requests.get(
        LIFI_QUOTE_URL,
        params=params,
        headers={"accept": "application/json", "user-agent": "tycho-topology-analysis/1.0"},
        timeout=45,
    )
    response.raise_for_status()
    return response.json()


def tenderly_bundle(args: TopologyArgs, quote: dict) -> dict:
    token = quote["action"]["fromToken"]["address"]
    amount = int(quote["action"]["fromAmount"])
    tx = quote["transactionRequest"]
    access_key = require_env("TENDERLY_ACCESS_KEY")
    account = os.environ.get("TENDERLY_ACCOUNT_SLUG", "leovigna")
    project = os.environ.get("TENDERLY_PROJECT_SLUG", "project")
    url = f"https://api.tenderly.co/api/v2/account/{account}/project/{project}/simulations/simulate/bundle"

    calls = [
        {
            "network_id": CHAIN_ID,
            "call_args": {
                "from": args.sender,
                "to": token,
                "gas": 200000,
                "gas_price": "0",
                "value": "0",
                "data": encode_approve(tx["to"], amount),
            },
        },
        {
            "network_id": CHAIN_ID,
            "call_args": {
                "from": args.sender,
                "to": tx["to"],
                "gas": int(args.gas),
                "gas_price": "0",
                "value": str(int(tx.get("value", "0x0"), 16) if str(tx.get("value", "0")).startswith("0x") else tx.get("value", "0")),
                "data": tx["data"],
            },
        },
    ]
    response = requests.post(
        url,
        headers={"X-Access-Key": access_key, "Content-Type": "application/json"},
        json={
            "network_id": CHAIN_ID,
            "call_args": [call["call_args"] for call in calls],
            "block_number_or_hash": {"blockNumber": latest_block_number()},
        },
        timeout=90,
    )
    if response.status_code >= 400:
        print(response.text[:2000], file=sys.stderr)
    response.raise_for_status()
    return response.json()


def latest_block_number() -> int:
    response = requests.post(
        "https://ethereum-rpc.publicnode.com",
        json={"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []},
        timeout=20,
    )
    response.raise_for_status()
    return int(response.json()["result"], 16)


def iter_logs(obj):
    if isinstance(obj, dict):
        if isinstance(obj.get("logs"), list):
            for item in obj["logs"]:
                yield item
        for value in obj.values():
            yield from iter_logs(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_logs(item)


def extract_transfer_logs(simulation: dict, sender: str) -> list[dict]:
    transfers = []
    seen = set()
    for log in iter_logs(simulation):
        topics = log.get("topics") or log.get("raw", {}).get("topics")
        data = log.get("data") or log.get("raw", {}).get("data")
        address = log.get("address") or log.get("raw", {}).get("address")
        if not topics or topics[0].lower() != TRANSFER_TOPIC or len(topics) < 3 or not data:
            continue
        token = normalize_address(address)
        if token.lower() not in TOKENS:
            continue
        from_addr = normalize_address(topics[1])
        to_addr = normalize_address(topics[2])
        amount = int(data, 16)
        key = (token.lower(), from_addr.lower(), to_addr.lower(), amount)
        if key in seen:
            continue
        seen.add(key)
        transfers.append(
            {
                "token": token,
                "token_symbol": TOKENS[token.lower()][0],
                "from": from_addr,
                "to": to_addr,
                "amount_raw": str(amount),
                "amount": token_amount(token, amount),
                "from_label": label(from_addr, sender),
                "to_label": label(to_addr, sender),
            }
        )
    return transfers


def iter_calls(obj):
    if isinstance(obj, dict):
        from_addr = obj.get("from")
        to_addr = obj.get("to")
        if from_addr and to_addr:
            yield normalize_address(from_addr), normalize_address(to_addr)
        for key in ("calls", "children", "subtraces", "trace", "call_trace"):
            value = obj.get(key)
            if value is not None:
                yield from iter_calls(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_calls(item)


def extract_known_calls(simulation: dict, sender: str) -> list[dict]:
    calls = []
    seen = set()
    for from_addr, to_addr in iter_calls(simulation):
        if to_addr.lower() not in KNOWN_CONTRACTS and from_addr.lower() not in KNOWN_CONTRACTS:
            continue
        key = (from_addr.lower(), to_addr.lower())
        if key in seen:
            continue
        seen.add(key)
        calls.append(
            {
                "from": from_addr,
                "to": to_addr,
                "from_label": label(from_addr, sender),
                "to_label": label(to_addr, sender),
            }
        )
    return calls


def simulation_results(bundle: dict) -> list[dict]:
    for key in ("simulation_results", "simulations", "results"):
        value = bundle.get(key)
        if isinstance(value, list):
            return value
    return []


def analyze_lifi_topology(args: TopologyArgs) -> None:
    load_default_env_files()
    quote = fetch_lifi_quote(args)
    bundle = tenderly_bundle(args, quote)
    results = simulation_results(bundle)
    if len(results) < 2:
        raise SystemExit(f"Unexpected Tenderly bundle response shape: {json.dumps(bundle)[:1000]}")

    swap_result = results[-1]
    transfers = extract_transfer_logs(swap_result, args.sender)
    calls = extract_known_calls(swap_result, args.sender)

    if args.save_prefix:
        Path(f"{args.save_prefix}.quote.json").write_text(json.dumps(quote, indent=2))
        Path(f"{args.save_prefix}.bundle.json").write_text(json.dumps(bundle, indent=2))

    print("Quote")
    print(f"  tool: {quote.get('tool') or (quote.get('includedSteps') or [{}])[-1].get('tool')}")
    print(f"  fromAmount: {quote['action']['fromAmount']}")
    print(f"  estimatedToAmount: {quote['estimate']['toAmount']}")
    print(f"  txTo: {quote['transactionRequest']['to']}")
    print()
    print("Simulation")
    print(f"  approve status: {results[0].get('status')}")
    print(f"  swap status: {swap_result.get('status')}")
    print(f"  swap gas used: {swap_result.get('gas_used') or swap_result.get('gasUsed')}")
    print()
    print("Realized token-transfer topology")
    for transfer in transfers:
        print(
            f"  {transfer['amount']:>28}  "
            f"{transfer['from_label']} -> {transfer['to_label']}"
        )
    print()
    print("Known venue/aggregator call topology")
    for call in calls:
        print(f"  {call['from_label']} -> {call['to_label']}")
