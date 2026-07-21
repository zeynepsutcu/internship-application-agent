# Staj Basvuru Ajani

Excel'deki firma listesindeki her sirket icin Claude'a CV'yi (PDF) ve web_search aracini vererek firmayi arastirtir, firmanin kendi ifadelerine (or. "DNA'miz") gonderme yapan ozgun bir Turkce staj basvuru metni uretir ve onayindan sonra Gmail uzerinden CV ekiyle gonderir.

## Nasil calisir

- `scripts/research_and_draft.py`: Excel'deki her firma icin Claude'a CV'yi (PDF olarak) ve web_search aracini vererek firmayi arastirtir, firmanin kendi ifadelerine gonderme yapan ozgun bir Turkce basvuru metni uretir ve `drafts/<firma>.txt` icine kaydeder. Zaten taslagi olan firmayi atlar, yani script tekrar tekrar guvenle calistirilabilir.
- `scripts/send_emails.py`: `drafts/` icindeki her taslagi tek tek ekrana basar, onay ister (e/h/q), onaylanirsa Gmail SMTP + App Password ile CV eki ile gonderir. Gonderilenleri `sent/` altinda isaretler, tekrar gondermez.

## Kurulum

1. CV'ni `cv/CV.pdf` olarak koy.
2. Firma listeni `data/companies.xlsx` olarak koy. Sutunlar: Firma Adi, Email, (opsiyonel) Website, Not.
3. `.env.example` dosyasini `.env` olarak kopyala, kendi bilgilerinle doldur. Gmail App Password icin: Google Hesap, Guvenlik, 2 Adimli Dogrulama acik olmali, ardindan Uygulama Sifreleri bolumunden olustur.
4. Bagimliliklari kur:

   ```
   pip install -r requirements.txt
   ```

## Kullanim

1. Taslaklari olustur:

   ```
   python scripts/research_and_draft.py
   ```

   Uretilen taslaklari `drafts/` altinda incele.

2. Onayladiklarini gonder:

   ```
   python scripts/send_emails.py
   ```

## Notlar

- CV, firma listesi, taslaklar ve gonderim kayitlari kisisel veri oldugu icin git'e gitmez (bkz. `.gitignore`).
- Hicbir mail onayin olmadan gonderilmez.
