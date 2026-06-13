#!/usr/bin/env bash
set -euo pipefail

SELL_TOKEN="${SELL_TOKEN:-0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48}"
BUY_TOKEN="${BUY_TOKEN:-0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2}"
AMOUNT_IN="${AMOUNT_IN:-1000000}"
CHAIN_ID="${CHAIN_ID:-1}"
FROM_ADDRESS="${FROM_ADDRESS:-0x0000000000000000000000000000000000000001}"

TYCHO_DIRECT_URL="${TYCHO_DIRECT_URL:-http://127.0.0.1:8099/quote/direct}"
LIFI_API_URL="${LIFI_API_URL:-https://li.quest/v1}"

require() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing required command: $1" >&2
    exit 1
  }
}

curl_json() {
  local body_file status
  body_file="$(mktemp)"
  status="$(curl -sS -o "$body_file" -w '%{http_code}' "$@")"
  printf '%s\t%s\n' "$status" "$body_file"
}

print_provider_result() {
  local provider="$1" status="$2" body_file="$3" jq_filter="$4"

  if [[ "$status" =~ ^2 ]]; then
    jq -r --arg provider "$provider" "$jq_filter" "$body_file"
  else
    printf '%s\tstatus=%s\t%s\n' "$provider" "$status" "$(head -c 300 "$body_file" | tr '\n' ' ')"
  fi
}

require curl
require jq

echo "quote input:"
echo "  chainId=$CHAIN_ID"
echo "  sellToken=$SELL_TOKEN"
echo "  buyToken=$BUY_TOKEN"
echo "  amountIn=$AMOUNT_IN"
echo
echo "provider results:"

read -r tycho_status tycho_body < <(
  curl_json -X POST "$TYCHO_DIRECT_URL" \
    -H 'Content-Type: application/json' \
    --data "$(jq -n \
      --arg sellToken "$SELL_TOKEN" \
      --arg buyToken "$BUY_TOKEN" \
      --arg amountIn "$AMOUNT_IN" \
      '{
        sellToken: $sellToken,
        buyToken: $buyToken,
        amountIn: $amountIn,
        minAmountOut: "1"
      }')"
)

print_provider_result "tycho-direct" "$tycho_status" "$tycho_body" '
  [
    $provider,
    "status=200",
    ("amountOut=" + (.bestQuote.amountOut // "null")),
    ("formatted=" + (.bestQuote.formattedAmountOut // "null")),
    ("protocol=" + (.bestQuote.protocol // "null")),
    ("pool=" + (.bestQuote.pool // "null")),
    ("candidates=" + (.successfulQuoteCount | tostring))
  ] | @tsv
'

read -r lifi_status lifi_body < <(
  curl_json --get "$LIFI_API_URL/quote" \
    --data-urlencode "fromChain=$CHAIN_ID" \
    --data-urlencode "toChain=$CHAIN_ID" \
    --data-urlencode "fromToken=$SELL_TOKEN" \
    --data-urlencode "toToken=$BUY_TOKEN" \
    --data-urlencode "fromAmount=$AMOUNT_IN" \
    --data-urlencode "fromAddress=$FROM_ADDRESS"
)

print_provider_result "lifi-no-key" "$lifi_status" "$lifi_body" '
  [
    $provider,
    "status=200",
    ("amountOut=" + (.estimate.toAmount // "null")),
    ("amountOutMin=" + (.estimate.toAmountMin // "null")),
    ("tool=" + (.tool // "null")),
    ("gas=" + ((.estimate.gasCosts[0].estimate // "null") | tostring))
  ] | @tsv
'

if [[ "${PROBE_LOCKED_PROVIDERS:-0}" == "1" ]]; then
  read -r oneinch_status oneinch_body < <(
    curl_json --get "https://api.1inch.com/swap/v6.1/$CHAIN_ID/quote" \
      --data-urlencode "src=$SELL_TOKEN" \
      --data-urlencode "dst=$BUY_TOKEN" \
      --data-urlencode "amount=$AMOUNT_IN"
  )
  print_provider_result "1inch-no-key" "$oneinch_status" "$oneinch_body" '. | @json'

  read -r uniswap_status uniswap_body < <(
    curl_json -X POST "https://trade-api.gateway.uniswap.org/v1/quote" \
      -H 'Content-Type: application/json' \
      --data "$(jq -n \
        --arg tokenIn "$SELL_TOKEN" \
        --arg tokenOut "$BUY_TOKEN" \
        --arg amount "$AMOUNT_IN" \
        --arg swapper "$FROM_ADDRESS" \
        --argjson chainId "$CHAIN_ID" \
        '{
          tokenIn: $tokenIn,
          tokenInChainId: $chainId,
          tokenOut: $tokenOut,
          tokenOutChainId: $chainId,
          amount: $amount,
          type: "EXACT_INPUT",
          swapper: $swapper
        }')"
  )
  print_provider_result "uniswap-no-key" "$uniswap_status" "$uniswap_body" '. | @json'
fi

rm -f "$tycho_body" "$lifi_body" "${oneinch_body:-}" "${uniswap_body:-}"
