#!/usr/bin/env bash
set -euo pipefail
seconds="${1:-30}"
if ! [[ "$seconds" =~ ^[0-9]+$ ]] || ((seconds<5 || seconds>60)); then echo 'Use 5..60 seconds'; exit 2; fi
run="$(date -u +%Y%m%dT%H%M%SZ)-$$"
out="/var/lib/cr-dos/zeek/$run"
sudo install -d -m 0755 -o "$(id -u)" -g "$(id -g)" "$out"
curl --fail --silent --show-error --max-time 75 "http://10.10.0.30:8081/capture?seconds=$seconds" -o "$out/capture.pcap"
image="$(cat /opt/cr-dos/zeek-image.txt)"
sudo docker run --rm --network none --read-only --tmpfs /tmp --user "$(id -u):$(id -g)" \
  --entrypoint /bin/sh -v "$out:/work" -w /work "$image" \
  -c 'exec zeek -C -r capture.pcap LogAscii::use_json=T'
echo "Real PCAP and Zeek JSON logs: $out"
echo 'Copy the relevant files to your own evidence folder before the sandbox is released.'
