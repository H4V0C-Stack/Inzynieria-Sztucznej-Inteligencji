# Inzynieria-Sztucznej-Inteligencji

# Jakość wina 
Pierwszy etap:

Kompleksowa analiza danych UCI Wine Quality i Wine Reviews oraz pytania badawcze.
Cały kod znajduje się w pliku `analiza_wina.ipynb`. Notebook korzysta z lokalnych danych i nie trenuje modeli.

## Uruchomienie

1. Zainstaluj wymagane zależności w środowisku Python:

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Otwórz `analiza_wina.ipynb` w Jupyter lub VS Code i uruchom wszystkie komórki od góry do dołu.
   W Google Colab najpierw prześlij i rozpakuj folder projektu, a następnie przejdź do niego przed uruchomieniem.
   Wskazówka: Notebook automatycznie zapisuje wygenerowane wykresy w `output/figures oraz` tabele w `output/tables`.

3. Przeglądanie wyników w interfejsie (Gradio):

   ```powershell
   python app.py
   ```

   Otwórz wskazany w terminalu adres (standardowo http://127.0.0.1:7860).
   Dostępne zakładки: dane liczbowe (rozkłady i korelacje), recenzje (filtry, próbki, analiza słów), tabele oraz wykresy.
   (Aby zatrzymać serwer, użyj kombinacji Ctrl+C w terminalu).

4. Raport PDF etapu 1 (opcjonalnie, odtworzenie):

   ```powershell
   python report/build_report.py
   ```

   Skrypt czyta zespół i adres repozytorium z `report/team.json` oraz tabele z `output/tables`.

Python 3.10+. Dane są już w `data/raw` — notebook ich nie pobiera. Nie wymaga internetu ani GPU.

## Pliki

```text
analiza_wina.ipynb        analiza EDA, testy statystyczne, pytania badawcze
app.py                    przeglądarka wyników (Gradio)
requirements.txt
data/
  raw/                    pliki źródłowe (4 pliki)
  sources.json            adresy źródłowe, daty pobrania, sumy kontrolne
output/
  analiza_danych_i_pytania_badawcze.pdf   raport etapu 1 (do wysłania na Platon)
  figures/                wykresy PNG
  tables/                 tabele CSV
report/
  build_report.py         generator raportu PDF
  team.json               skład zespołu i adres repozytorium
```

Notebook przelicza analizę i zapisuje wykresy PNG oraz tabele CSV; raport PDF powstaje osobno
(`report/build_report.py`). `data/sources.json` zawiera adresy źródłowe i sumy kontrolne:
`sha256` dotyczy pliku pobranego ze źródła, a `repo_sha256` pliku w tym repozytorium. Dla `winequality.names`
i `winemag-data-130k-v2.csv` obie sumy się różnią (różnica kilku bajtów, prawdopodobnie normalizacja końców linii
przez git przy pierwszym dodaniu plików). Plik `.gitattributes` zapobiega dalszym zmianom.

## Zakres analizy

- Braki danych, powtórzenia, statystyki opisowe i obserwacje odstające według reguły IQR.
- Rozkład ocen i korelacje Spearmana osobno dla win czerwonych i białych.
- Rozkłady ocen i długości recenzji oraz zależności ceny i długości opisu od oceny.
- Porównanie częstości słów w grupach `points >= 90` i `points <= 85`.
- Rozkłady cech fizykochemicznych, korelacje między cechami (wielokolinearność), testy normalności.
- Testy statystyczne: Mann–Whitney (czerwone vs białe), korelacje Spearmana z przedziałami ufności i korektą Bonferroniego,
  Kruskal–Wallis (alkohol a jakość; oceny a kraj, odmiana, autor recenzji), chi-kwadrat dla słownictwa, wielkości efektu.
- Cztery pytania badawcze z hipotezami i planem weryfikacji.

Po usunięciu powtórzeń pozostaje 1359 czerwonych i 3961 białych win oraz 119954 recenzji.
Cena jest dostępna dla 111566 oczyszczonych recenzji. Nie uzupełniamy brakujących cen ani nie usuwamy
automatycznie obserwacji odstających. Przy powtórzeniach zachowujemy pierwsze wystąpienie;
dla opisów normalizujemy wielkość liter i białe znaki.

Zbiory dotyczą różnych win oraz używają różnych skal ocen, dlatego nie łączymy rekordów.
Korelacje i różnice słownictwa opisują tę próbę, a nie zależności przyczynowe.

## Zespół

| Osoba | ID | Zakres pracy |
|---|---|---|
| Lavrenko Nazarii | 71499 | Pozyskanie i czyszczenie danych liczbowych (UCI Wine Quality), `data/sources.json` |
| Dorokhin Yevhenii | 71545 | EDA zbioru recenzji (dane tekstowe), analiza słownictwa |
| Kelyp Yaroslav | 71503 | Testy statystyczne, przedziały ufności i wielkości efektu (sekcja 5 notebooka) |
| Pitsukha Herman | 71682 | Repozytorium GitHub, README, przeglądarka wyników w Gradio (`app.py`) |
| Tsymbaliuk Roman | 71676 | Pytania badawcze, plan kolejnych etapów, redakcja raportu PDF |

## Źródła

- [UCI Wine Quality](https://archive.ics.uci.edu/dataset/186/wine%2Bquality), Cortez i in. (2009).
  [DOI: 10.24432/C56S3T](https://doi.org/10.24432/C56S3T), licencja **CC BY 4.0**.
  Pliki czerwonych i białych win pochodzą z tego samego zasobu.
- [Wine Reviews](https://www.kaggle.com/datasets/zynicide/wine-reviews), Zack Thoutt;
  opisy degustacyjne Wine Enthusiast, plik `winemag-data-130k-v2.csv`, licencja **CC BY-NC-SA 4.0**.
