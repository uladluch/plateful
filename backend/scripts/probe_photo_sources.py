#!/usr/bin/env python3
"""Разведка снимков: чем сайт сети отдаёт фотографии блюд.

    python3 backend/scripts/probe_photo_sources.py                 # все сети
    python3 backend/scripts/probe_photo_sources.py sonic wendy-s   # выбранные
    python3 backend/scripts/probe_photo_sources.py --json out.json
    python3 backend/scripts/probe_photo_sources.py --apply         # записать в chains

Для каждой сети зонд открывает её сайт (несколько привычных адресов
меню), смотрит, на какой платформе лежат снимки, и считает, сколько
фотографий блюд видно в разметке. Ответ — не «есть/нет», а **платформа**:
Olo, Sanity, Contentful, AEM, WordPress, Next.js, Scene7, Cloudflare
Images. Платформа важнее сети: один адаптер на Olo закрыл Chili's и
Applebee's, один на Contentful — пять сетей GoTo Foods. Новую сеть
подключают, узнав платформу, а не разбирая сайт с нуля.

Зонд читает только сайт самой сети — не площадки доставки и не чужие
каталоги. Сайты сетей отдают американское меню только с американского
адреса; с другого зонд увидит 403 или чужую локаль и так и запишет.

Печатает таблицу; с `--json` сохраняет разбор целиком, с `--apply` —
пишет его в `chains.photo_probe`, чтобы знание накапливалось, как у
`vacuum.py`: следующий агент читает, а не разведывает заново.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plateful_data.adapters.base import BROWSER_HEADERS, curl_get

#: Сайт сети. Единственное, что нужно знать заранее: национальный сайт
#: США, не страница франшизы.
WEBSITES = {
    "7-eleven": "7-eleven.com", "applebee-s": "applebees.com", "arby-s": "arbys.com",
    "auntie-anne-s": "auntieannes.com", "baskin-robbins": "baskinrobbins.com",
    "bj-s-restaurant-brewhouse": "bjsrestaurants.com", "bob-evans": "bobevans.com",
    "bojangles": "bojangles.com", "bonefish-grill": "bonefishgrill.com",
    "boston-market": "bostonmarket.com", "burger-king": "bk.com",
    "california-pizza-kitchen": "cpk.com", "captain-d-s": "captainds.com",
    "carl-s-jr": "carlsjr.com", "carrabba-s-italian-grill": "carrabbas.com",
    "casey-s-general-store": "caseys.com", "checker-s-drive-in-rallys": "checkers.com",
    "chick-fil-a": "chick-fil-a.com", "chili-s": "chilis.com", "chipotle": "chipotle.com",
    "chuck-e-cheese": "chuckecheese.com", "church-s-chicken": "churchs.com",
    "ci-ci-s-pizza": "cicis.com", "culver-s": "culvers.com", "dairy-queen": "dairyqueen.com",
    "del-taco": "deltaco.com", "denny-s": "dennys.com", "dickey-s-barbeque-pit": "dickeys.com",
    "dominos": "dominos.com", "dunkin-donuts": "dunkindonuts.com",
    "einstein-bros": "einsteinbros.com", "el-pollo-loco": "elpolloloco.com",
    "famous-dave-s": "famousdaves.com", "firehouse-subs": "firehousesubs.com",
    "five-guys": "fiveguys.com", "friendly-s": "friendlys.com", "frisch-s-big-boy": "frischs.com",
    "golden-corral": "goldencorral.com", "hardee-s": "hardees.com", "hooters": "hooters.com",
    "ihop": "ihop.com", "in-n-out-burger": "in-n-out.com", "jack-in-the-box": "jackinthebox.com",
    "jamba-juice": "jamba.com", "jason-s-deli": "jasonsdeli.com",
    "jersey-mike-s-subs": "jerseymikes.com", "jimmy-john-s": "jimmyjohns.com",
    "joe-s-crab-shack": "joescrabshack.com", "kfc": "kfc.com", "krispy-kreme": "krispykreme.com",
    "krystal": "krystal.com", "little-caesars": "littlecaesars.com",
    "long-john-silver-s": "ljsilvers.com", "longhorn-steakhouse": "longhornsteakhouse.com",
    "marco-s-pizza": "marcos.com", "mcalister-s-deli": "mcalistersdeli.com",
    "mcdonald-s": "mcdonalds.com", "moe-s-southwest-grill": "moes.com",
    "noodles-company": "noodles.com", "o-charley-s": "ocharleys.com",
    "olive-garden": "olivegarden.com", "on-the-border": "ontheborder.com",
    "outback-steakhouse": "outback.com", "panda-express": "pandaexpress.com",
    "panera-bread": "panerabread.com", "papa-john-s": "papajohns.com",
    "papa-murphy-s": "papamurphys.com", "perkins": "perkinsrestaurants.com",
    "pf-chang-s": "pfchangs.com", "pizza-hut": "pizzahut.com", "popeyes": "popeyes.com",
    "potbelly-sandwich-shop": "potbelly.com", "qdoba": "qdoba.com", "quiznos": "quiznos.com",
    "red-lobster": "redlobster.com", "red-robin": "redrobin.com",
    "romano-s-macaroni-grill": "macaronigrill.com", "round-table-pizza": "roundtablepizza.com",
    "ruby-tuesday": "rubytuesday.com", "sbarro": "sbarro.com", "sheetz": "sheetz.com",
    "sonic": "sonicdrivein.com", "starbucks": "starbucks.com", "steak-n-shake": "steaknshake.com",
    "subway": "subway.com", "taco-bell": "tacobell.com", "tgi-friday-s": "tgifridays.com",
    "the-capital-grille": "thecapitalgrille.com", "tim-hortons": "timhortons.com",
    "wawa": "wawa.com", "wendy-s": "wendys.com", "whataburger": "whataburger.com",
    "white-castle": "whitecastle.com", "wingstop": "wingstop.com", "yard-house": "yardhouse.com",
    "zaxby-s": "zaxbys.com",
}

#: Привычные адреса меню. Первый, что отдал настоящую страницу, и есть ответ.
MENU_PATHS = ("/menu", "/food", "/en/menu", "/en-us/menu", "/order/menu",
              "/menu.html", "/us/en/menu", "/")

#: Признаки платформы — по порядку от точных к общим. Побеждают все, что
#: нашлись: у сети может быть Next.js поверх Contentful.
SIGNALS = (
    ("olo",        re.compile(r"olo-images-live\.imgix\.net|\"(?:oloProductId|ChainProductId)\"")),
    ("sanity",     re.compile(r"cdn\.sanity\.io")),
    ("contentful", re.compile(r"ctfassets\.net|/contentful\b")),
    ("aem",        re.compile(r"/content/dam/|\.asset\.json")),
    ("scene7",     re.compile(r"scene7\.com/is/image")),
    ("wordpress",  re.compile(r"/wp-content/uploads/")),
    ("cloudflare-images", re.compile(r"imagedelivery\.net")),
    ("nextjs",     re.compile(r"__NEXT_DATA__|self\.__next_f")),
    ("nuxt",       re.compile(r"__NUXT__")),
    ("ld-json",    re.compile(r'type="application/ld\+json"')),
)

_IMAGE = re.compile(r'https://[^"\'\\ )]+?\.(?:jpg|jpeg|png|webp)', re.I)
_JUNK = re.compile(r"logo|icon|sprite|favicon|placeholder|banner|hero|badge|social", re.I)
#: Только слова, которых в американской разметке не бывает. «Commander»
#: и «Panier» сюда нельзя: у Marco's и Bojangles в списке адресов лежит
#: «Commander Shepard Blvd», и обе сети попадали в «чужую локаль».
_FOREIGN = re.compile(r"Wprowadź|Zamów|\bzł\b|Menü|Bestellen|Warenkorb")
#: Меньше — не страница меню, а оболочка, которую дорисует скрипт.
SHELL = 15 * 1024


@dataclass
class Probe:
    slug: str
    website: str
    url: str | None
    size_kb: int
    platforms: list[str]
    images: int
    verdict: str
    note: str = ""


def probe(slug: str) -> Probe:
    website = WEBSITES[slug]
    best: tuple[str, str] | None = None
    for path in MENU_PATHS:
        url = f"https://www.{website}{path}"
        body = curl_get(url, BROWSER_HEADERS, timeout=45) or ""
        if _FOREIGN.search(body):
            return Probe(slug, website, url, len(body) // 1024, [], 0,
                         "чужая локаль", "сайт показал не американское меню")
        if len(body) >= SHELL:
            best = (url, body)
            break
        if body and best is None:
            best = (url, body)
    if best is None:
        return Probe(slug, website, None, 0, [], 0, "не открылся",
                     "403, обрыв или пустой ответ на всех адресах")
    url, body = best
    platforms = [name for name, pattern in SIGNALS if pattern.search(body)]
    images = len({u.split("?")[0] for u in _IMAGE.findall(body) if not _JUNK.search(u)})
    if len(body) < SHELL:
        verdict = "оболочка, меню рисует скрипт"
    elif images >= 20:
        verdict = "снимки в разметке"
    elif any(p in platforms for p in ("olo", "sanity", "contentful", "aem", "nextjs")):
        verdict = "данные есть, снимки на страницах разделов или в API"
    else:
        verdict = "снимков не видно"
    return Probe(slug, website, url, len(body) // 1024, platforms, images, verdict)


def record(results: list[Probe]) -> None:
    """Разбор — в `chains.photo_probe`, одной командой на все сети."""
    statements = []
    for r in results:
        payload = json.dumps({"url": r.url, "platforms": r.platforms, "images": r.images,
                              "verdict": r.verdict, "note": r.note}, ensure_ascii=False)
        payload = payload.replace("'", "''")
        statements.append(f"update chains set photo_probed_at = now(), photo_probe = "
                          f"'{payload}'::jsonb where slug = '{r.slug}';")
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as fh:
        fh.write("\n".join(statements))
        path = fh.name
    try:
        subprocess.run(["supabase", "db", "query", "--linked", "--agent=no", "-f", path],
                       check=True, capture_output=True, text=True)
    finally:
        Path(path).unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("chains", nargs="*")
    parser.add_argument("--json", type=Path, help="куда сохранить разбор целиком")
    parser.add_argument("--apply", action="store_true", help="записать разбор в chains")
    parser.add_argument("--from-json", type=Path,
                        help="не ходить по сайтам: взять разбор из файла и записать его")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    if args.from_json:
        results = [Probe(**r) for r in json.loads(args.from_json.read_text(encoding="utf-8"))]
        record(results)
        print(f"записано в chains из {args.from_json}: {len(results)} сетей")
        return 0

    slugs = args.chains or sorted(WEBSITES)
    unknown = [s for s in slugs if s not in WEBSITES]
    if unknown:
        raise SystemExit(f"сайт не записан: {', '.join(unknown)}")

    print(f"{'сеть':26} {'КБ':>5} {'снимков':>7}  платформы                       вывод")
    results: list[Probe] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(probe, slugs):
            results.append(result)
            print(f"{result.slug:26} {result.size_kb:5} {result.images:7}  "
                  f"{', '.join(result.platforms)[:30]:30}  {result.verdict}", flush=True)
    if args.json:
        args.json.write_text(json.dumps([asdict(r) for r in results], ensure_ascii=False,
                                        indent=1), encoding="utf-8")
        print(f"\nразбор сохранён: {args.json}")
    if args.apply:
        record(results)
        print(f"записано в chains: {len(results)} сетей")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
