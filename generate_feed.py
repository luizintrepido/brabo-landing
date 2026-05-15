"""
Gerador de feed XML para Meta Catalog (Automotive Inventory Ads)
Fonte: https://luizintrepido.github.io/catalogo-brabo/vehicles.json
Saída: feed.xml (hospedado no GitHub Pages do brabo-landing)
"""

import json
import urllib.request
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent
from datetime import datetime, timezone

VEHICLES_URL = "https://luizintrepido.github.io/catalogo-brabo/vehicles.json"
LANDING_URL  = "https://luizintrepido.github.io/brabo-landing"
OUTPUT_FILE  = "feed.xml"

DRIVE_IMG = "https://lh3.googleusercontent.com/d/{}=s800"

TRANSMISSION_MAP = {
    "automático": "Automatic",
    "automatico": "Automatic",
    "manual": "Manual",
    "cvt": "CVT",
}

FUEL_MAP = {
    "flex": "Flex-fuel",
    "gasolina": "Gasoline",
    "diesel": "Diesel",
    "elétrico": "Electric",
    "eletrico": "Electric",
    "híbrido": "Hybrid",
    "hibrido": "Hybrid",
}

BODY_MAP = {
    "suv": "SUV",
    "hatch": "Hatchback",
    "sedan": "Sedan",
    "picape": "Pickup Truck",
    "pickup": "Pickup Truck",
    "van": "Van/Minivan",
    "esportivo": "Coupe",
    "outros": "Other",
}


def norm(val, mapping):
    if not val:
        return ""
    return mapping.get(str(val).lower().strip(), str(val))


def fetch_vehicles():
    with urllib.request.urlopen(VEHICLES_URL, timeout=20) as r:
        data = json.loads(r.read().decode())
    if isinstance(data, list):
        return data
    return data.get("vehicles", data.get("veiculos", []))


def first_img(v):
    fotos = v.get("fotos_drive") or v.get("fotos") or []
    if fotos:
        fid = fotos[0] if isinstance(fotos[0], str) else fotos[0].get("id", "")
        if fid:
            return DRIVE_IMG.format(fid)
    if v.get("img"):
        return v["img"]
    return f"{LANDING_URL}/em-preparacao.jpg"


def build_description(v):
    parts = []
    if v.get("versao"):
        parts.append(v["versao"])
    if v.get("ano"):
        parts.append(f"Ano {v['ano']}")
    if v.get("km"):
        parts.append(f"{int(v['km']):,} km".replace(",", "."))
    if v.get("combustivel"):
        parts.append(v["combustivel"])
    if v.get("cambio"):
        parts.append(v["cambio"])
    if v.get("cor"):
        parts.append(v["cor"])
    base = " | ".join(parts) if parts else "Veículo usado em ótimo estado"
    return f"{v.get('marca','')} {v.get('modelo','')} - {base}. Laudo cautelar aprovado, garantia de até 2 anos. Fale com O Brabo das Vendas!".strip()


def generate_feed(vehicles):
    # Root: RSS 2.0
    rss = Element("rss", {
        "version": "2.0",
        "xmlns:g": "http://base.google.com/ns/1.0",
    })
    channel = SubElement(rss, "channel")

    SubElement(channel, "title").text = "O Brabo das Vendas — Estoque de Veículos"
    SubElement(channel, "link").text = LANDING_URL
    SubElement(channel, "description").text = (
        "Estoque de veículos seminovos e usados da Recar Automarcas / Grupo Reauto Veículos. "
        "Laudo cautelar aprovado, garantia até 2 anos, financiamento facilitado."
    )
    SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S +0000"
    )

    added = set()
    for v in vehicles:
        vid = str(v.get("id") or "").strip()
        if not vid or vid in added:
            continue
        if not v.get("preco") or int(v.get("preco", 0)) <= 0:
            continue
        added.add(vid)

        item = SubElement(channel, "item")

        SubElement(item, "g:id").text = vid
        title = f"{v.get('marca','')} {v.get('modelo','')} {v.get('ano','')}"
        SubElement(item, "g:title").text = title.strip()
        SubElement(item, "g:description").text = build_description(v)
        SubElement(item, "g:availability").text = "in stock"
        SubElement(item, "g:condition").text = "used"

        preco_fmt = f"{int(v['preco']):.2f} BRL"
        SubElement(item, "g:price").text = preco_fmt

        link = f"{LANDING_URL}/#estoque"
        SubElement(item, "g:link").text = link
        SubElement(item, "g:image_link").text = first_img(v)

        SubElement(item, "g:brand").text = str(v.get("marca") or "").title()
        SubElement(item, "g:make").text = str(v.get("marca") or "").title()
        SubElement(item, "g:model").text = str(v.get("modelo") or "")

        if v.get("ano"):
            SubElement(item, "g:year").text = str(int(v["ano"]))

        if v.get("km"):
            m = SubElement(item, "g:mileage")
            m.set("value", str(int(v["km"])))
            m.set("unit", "KM")

        if v.get("tipo"):
            bs = norm(v["tipo"], BODY_MAP)
            if bs:
                SubElement(item, "g:body_style").text = bs

        if v.get("combustivel"):
            ft = norm(v["combustivel"], FUEL_MAP)
            if ft:
                SubElement(item, "g:fuel_type").text = ft

        if v.get("cambio"):
            tr = norm(v["cambio"], TRANSMISSION_MAP)
            if tr:
                SubElement(item, "g:transmission").text = tr

        if v.get("versao"):
            SubElement(item, "g:trim").text = str(v["versao"])

        if v.get("cor"):
            SubElement(item, "g:exterior_color").text = str(v["cor"])

        # VIN/ID do veículo como identificador adicional
        SubElement(item, "g:vehicle_id").text = vid

    return rss


def main():
    print("Buscando veículos...")
    vehicles = fetch_vehicles()
    print(f"Encontrados: {len(vehicles)} veículos")

    rss = generate_feed(vehicles)
    indent(rss, space="  ")

    tree = ElementTree(rss)
    tree.write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)

    # Conta itens gerados
    items = rss.find("channel").findall("item")
    print(f"Feed gerado: {OUTPUT_FILE} ({len(items)} itens)")
    print(f"URL do feed: https://luizintrepido.github.io/brabo-landing/feed.xml")


if __name__ == "__main__":
    main()
