#!/usr/bin/env bash
# Run ON the DigitalOcean droplet. Prints NDJSON diagnostics for Cloudflare 521.
# Usage: bash scripts/diagnose_cf521.sh
# Paste the full output back into the debug session.

set -u
TS=$(date +%s%3N 2>/dev/null || date +%s000)
SID=a907ab

emit() {
  local hid="$1" msg="$2" data="$3"
  printf '{"sessionId":"%s","hypothesisId":"%s","location":"diagnose_cf521.sh","message":"%s","data":%s,"timestamp":%s}\n' \
    "$SID" "$hid" "$msg" "$data" "$TS"
}

# H1: nginx not running / not listening
NGINX_ACTIVE=$(systemctl is-active nginx 2>/dev/null || echo unknown)
LISTEN=$(ss -tlnp 2>/dev/null | grep -E ':80 |:443 |:3000 ' | tr '\n' ';' | sed 's/"/\\"/g' || echo "")
emit "H1" "nginx_and_listeners" "{\"nginx\":\"$NGINX_ACTIVE\",\"listeners\":\"$LISTEN\"}"

# H2: no TLS on :443 while Cloudflare Full/strict
HAS80=$(ss -tlnp 2>/dev/null | grep -c ':80 ' || true)
HAS443=$(ss -tlnp 2>/dev/null | grep -c ':443 ' || true)
emit "H2" "ports_80_443" "{\"count80\":$HAS80,\"count443\":$HAS443}"

# H3: firewall blocking
UFW=$(sudo ufw status 2>/dev/null | head -20 | tr '\n' ';' | sed 's/"/\\"/g' || echo "ufw_unavailable")
emit "H3" "firewall" "{\"ufw\":\"$UFW\"}"

# H4: nginx config / site enabled
NGINX_T=$(sudo nginx -t 2>&1 | tr '\n' ';' | sed 's/"/\\"/g')
ENABLED=$(ls -la /etc/nginx/sites-enabled/ 2>/dev/null | tr '\n' ';' | sed 's/"/\\"/g')
emit "H4" "nginx_config" "{\"nginx_t\":\"$NGINX_T\",\"sites_enabled\":\"$ENABLED\"}"

# H5: local origin responds on HTTP
LOCAL80=$(curl -sS -o /tmp/dd_cf521_body.txt -w "%{http_code}" -H "Host: diet.yayati-labs.com" --connect-timeout 3 http://127.0.0.1/ 2>/dev/null || echo "curl_fail")
BODY_HEAD=$(head -c 120 /tmp/dd_cf521_body.txt 2>/dev/null | tr '\n' ' ' | sed 's/"/\\"/g')
emit "H5" "local_http_origin" "{\"http_code\":\"$LOCAL80\",\"body_head\":\"$BODY_HEAD\"}"

# Bonus: API health
API=$(curl -sS --connect-timeout 3 http://127.0.0.1:3000/health 2>/dev/null || echo "api_fail")
emit "H1" "api_health" "{\"body\":\"$(echo "$API" | sed 's/"/\\"/g')\"}"

echo "--- paste everything above into the debug chat ---" >&2
