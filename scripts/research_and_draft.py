"""Firma listesindeki her satir icin sirketi arastirir ve CV'ye ozel,
kisisellestirilmis bir staj basvuru e-postasi taslagi hazirlar.

Ciktilar drafts/ klasorune yazilir; hicbir mail gonderilmez.
Gonderim icin ayri script: scripts/send_emails.py
"""

import base64
import os
import sys
from pathlib import Path

import pandas as pd
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-opus-4-8"

ROOT = Path(__file__).resolve().parent.parent
CV_PATH = ROOT / os.environ.get("CV_PATH", "cv/CV.pdf")
COMPANIES_XLSX = ROOT / os.environ.get("COMPANIES_XLSX", "data/companies.xlsx")
DRAFTS_DIR = ROOT / "drafts"

COLUMN_ALIASES = {
    "firma_adi": ["firma adı", "firma adi", "şirket adı", "sirket adi", "company", "firma"],
    "email": ["email", "e-posta", "eposta", "mail", "e-mail"],
    "website": ["website", "site", "web sitesi", "url", "web"],
    "not_": ["not", "notlar", "sektör", "sektor", "sector", "notes", "aciklama", "açıklama"],
}


def find_column(columns, aliases):
    lowered = {str(c).strip().lower(): c for c in columns}
    for alias in aliases:
        if alias in lowered:
            return lowered[alias]
    return None


def load_companies():
    df = pd.read_excel(COMPANIES_XLSX)
    resolved = {}
    for key, aliases in COLUMN_ALIASES.items():
        col = find_column(df.columns, aliases)
        if col is None and key in ("firma_adi", "email"):
            raise ValueError(
                f"Excel dosyasinda '{key}' icin bir sutun bulunamadi. "
                f"Mevcut sutunlar: {list(df.columns)}"
            )
        resolved[key] = col

    companies = []
    for _, row in df.iterrows():
        companies.append(
            {
                "firma_adi": row[resolved["firma_adi"]],
                "email": row[resolved["email"]],
                "website": row[resolved["website"]] if resolved["website"] else None,
                "not_": row[resolved["not_"]] if resolved["not_"] else None,
            }
        )
    return companies


def load_cv_base64():
    return base64.standard_b64encode(CV_PATH.read_bytes()).decode("utf-8")


def draft_for_company(client, cv_b64, company):
    prompt = f"""Sen bir universite ogrencisinin uzun donem staj basvurusu icin
kisisellestirilmis e-posta metni yazan bir asistansin.

Firma: {company['firma_adi']}
Website: {company.get('website') or 'bilinmiyor'}
Ek not: {company.get('not_') or 'yok'}

Gorevin:
1. web_search araciyla bu firmanin web sitesini ve varsa "hakkimizda",
   "kultur", "degerler" gibi sayfalarini arastir.
2. Firmanin KENDI ifadeleriyle (slogan, deger, kultur tanimi vb.) CV'deki
   beceriler ve deneyimler arasinda somut, ozgun bir baglanti kur.
   Ornek: firma "DNA'miz" gibi bir ifade kullaniyorsa, adayin o DNA'ya
   nasil uydugunu somut CV detaylariyla anlat.
3. Turkce, samimi ama profesyonel, kisa (150-220 kelime) bir uzun donem
   staj basvuru e-postasi yaz.
4. Genel gecer, kopyala-yapistir hissi veren cumlelerden kesinlikle kacin.
5. CV'de olmayan hicbir beceri veya deneyim uydurma.

Ciktiyi TAM OLARAK su formatta ver, baska hicbir sey ekleme:

KONU: <e-posta konu satiri>
---
<e-posta govdesi>
"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 5}],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": cv_b64,
                        },
                        "title": "CV",
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    text_parts = [b.text for b in response.content if b.type == "text"]
    return "\n".join(text_parts).strip()


def safe_filename(name):
    return "".join(c if c.isalnum() else "_" for c in str(name)).strip("_")


def main():
    if not CV_PATH.exists():
        sys.exit(f"CV bulunamadi: {CV_PATH}\n-> CV'ni cv/ klasorune PDF olarak koy.")
    if not COMPANIES_XLSX.exists():
        sys.exit(
            f"Firma listesi bulunamadi: {COMPANIES_XLSX}\n"
            "-> Excel dosyani data/ klasorune koy (sutunlar: Firma Adi, Email, "
            "Website, Not)."
        )

    DRAFTS_DIR.mkdir(exist_ok=True)
    client = Anthropic()
    cv_b64 = load_cv_base64()
    companies = load_companies()

    for company in companies:
        name = str(company["firma_adi"]).strip()
        email = str(company["email"]).strip()
        if not email or email.lower() == "nan":
            print(f"[ATLANDI] {name}: e-posta adresi yok")
            continue

        draft_path = DRAFTS_DIR / f"{safe_filename(name)}.txt"
        if draft_path.exists():
            print(f"[ZATEN VAR] {name}")
            continue

        print(f"[ARASTIRILIYOR] {name} ...")
        try:
            draft = draft_for_company(client, cv_b64, company)
        except Exception as exc:
            print(f"[HATA] {name}: {exc}")
            continue

        draft_path.write_text(f"ALICI: {email}\n{draft}\n", encoding="utf-8")
        print(f"[TASLAK HAZIR] {draft_path.name}")

    print("\nTum taslaklar 'drafts/' klasorunde.")
    print("Gondermeden once mutlaka her taslagi gozden gecir.")
    print("Gonderim icin: python scripts/send_emails.py")


if __name__ == "__main__":
    main()
