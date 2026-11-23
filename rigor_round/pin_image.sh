#!/bin/bash
# Pin every rg- Job to one exact vivado-vitis image (the same one your pipeline / nrp-hls4ml runs passed on).
#   ./pin_image.sh                      -> takes the digest pinned in ~/hls4ml-paper/tool-test/nrp-hls4ml
#   ./pin_image.sh sha256:<64 hex>      -> or give it yourself (e.g. from /work/pipe/<design>/image_digest.txt)
set -e
DIG=${1:-$(grep -ho 'vivado-vitis@sha256:[0-9a-f]\{64\}' ~/hls4ml-paper/tool-test/nrp-hls4ml ~/hls4ml-paper/hls4ml_on_nrp/nrp-hls4ml 2>/dev/null | head -1 | cut -d@ -f2)}
[[ "$DIG" =~ ^sha256:[0-9a-f]{64}$ ]] || { echo "no full digest found; run ./pin_image.sh sha256:<64 hex>"; exit 1; }
for f in jobs/*.yaml rg-card.yaml; do
  sed -i.bak -E "s#(image: gitlab-registry.nrp-nautilus.io/nrp/coder-images/vivado-vitis)(@sha256:[0-9a-f]{64})?\$#\1@$DIG#" $f && rm -f $f.bak
done
grep -h "image:" jobs/*.yaml rg-card.yaml | sort | uniq -c
