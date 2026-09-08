#!/usr/bin/env bash
# Публикация пака: база → файл → Storage → запись о релизе.
#
#   ./backend/scripts/publish_pack.sh 3
#
# Пароль базы и service-ключ не нужны: всё делает supabase CLI по своему
# access-токену. Один раз локально: supabase login && supabase link.
set -euo pipefail

VERSION="${1:?Укажите версию: publish_pack.sh 3}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

DEFLATE="backend/data/pack-v${VERSION}.deflate"
MANIFEST="backend/data/manifest.json"
BASE_URL="https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/packs"

echo "── Сборка пака из базы ──"
python3 backend/scripts/export_pack.py --version "$VERSION"

echo "── Загрузка в Storage ──"
# Версии пака кэшируются как неизменяемые, поэтому подменять уже выложенный
# файл нельзя: у клиентов останется старая копия под тем же именем. Если
# версия уже лежит — сверяем содержимое. Совпало (например, повтор после
# сорвавшейся публикации) — пропускаем; разошлось — это ошибка, нужна новая
# версия, а не тихая подмена.
EXISTING=$(curl -s -o /tmp/existing.deflate -w "%{http_code}" \
  "$BASE_URL/v${VERSION}.deflate")
if [ "$EXISTING" = "200" ]; then
  if cmp -s /tmp/existing.deflate "$DEFLATE"; then
    echo "  v${VERSION} уже выложен и совпадает — пропускаю"
  else
    echo "  ОШИБКА: v${VERSION} уже выложен и отличается." >&2
    echo "  Неизменяемую версию подменять нельзя — публикуйте следующую." >&2
    exit 1
  fi
else
  supabase storage cp "$DEFLATE" "ss:///packs/v${VERSION}.deflate" \
    --linked --experimental --content-type application/octet-stream \
    --cache-control "max-age=31536000, immutable"
fi
rm -f /tmp/existing.deflate
# Манифест перезаписывается каждым релизом, но `storage cp` отказывается
# затирать существующий файл (409 KeyAlreadyExists), а флага upsert у него
# нет — поэтому сначала убираем старый. Пак так удалять нельзя и не нужно:
# его версии неизменяемы.
# --yes обязателен: без него rm спрашивает подтверждение и в скрипте
# молча висит, а `|| true` прячет это за успешным кодом возврата.
supabase storage rm "ss:///packs/manifest.json" --linked --experimental --yes >/dev/null 2>&1 || true
supabase storage cp "$MANIFEST" "ss:///packs/manifest.json" \
  --linked --experimental --content-type application/json \
  --cache-control "max-age=60"

echo "── Проверка публичной ссылки ──"
python3 - "$VERSION" <<'PY'
import hashlib, json, sys, urllib.request, zlib
version = sys.argv[1]
base = "https://tnlmtyhuuqpjwuhzximh.supabase.co/storage/v1/object/public/packs"
manifest = json.load(open("backend/data/manifest.json"))
with urllib.request.urlopen(f"{base}/v{version}.deflate", timeout=120) as response:
    raw = response.read()
assert hashlib.sha256(raw).hexdigest() == manifest["sha256"], "sha256 не совпал с манифестом"
pack = json.loads(zlib.decompressobj(-zlib.MAX_WBITS).decompress(raw))
assert len(pack["items"]) == manifest["itemCount"], "число позиций разошлось"
print(f"  ок: {len(pack['items']):,} позиций, версия {pack['version']}")
PY

echo "── Запись о релизе ──"
python3 - "$VERSION" "$BASE_URL" > /tmp/release.sql <<'PY'
import json, sys
version, base = sys.argv[1], sys.argv[2]
manifest = json.load(open("backend/data/manifest.json"))
print(f"""insert into releases (version, pack_url, sha256, item_count)
values ({version}, '{base}/v{version}.deflate', '{manifest["sha256"]}', {manifest["itemCount"]})
on conflict (version) do update set pack_url = excluded.pack_url,
  sha256 = excluded.sha256, item_count = excluded.item_count;""")
PY
supabase db query --linked -f /tmp/release.sql >/dev/null
rm -f /tmp/release.sql

echo "Пак v${VERSION} опубликован."
