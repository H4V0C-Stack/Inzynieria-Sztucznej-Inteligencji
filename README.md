# Inzynieria-Sztucznej-Inteligencji

# Jakość wina — pierwszy etap

Analiza danych UCI Wine Quality i Wine Reviews oraz pytania badawcze.
Cały kod jest w `analiza_wina.ipynb`. Notebook korzysta z lokalnych danych i nie trenuje modeli.

## Uruchomienie

1. Zainstaluj zależności:

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Otwórz `analiza_wina.ipynb` w Jupyter lub VS Code i uruchom wszystkie komórki od góry do dołu.
   W Colab prześlij i rozpakuj folder projektu, a następnie przejdź do niego przed uruchomieniem notebooka.

Python 3.10+. Dane są już w `data/raw` — notebook ich nie pobiera. Nie wymaga internetu ani GPU.

## Pliki

```text
analiza_wina.ipynb
analiza.pdf
czlonki_zespolu.pdf
requirements.txt
data/
  raw/
    winequality-red.csv
    winequality-white.csv
    winequality.names
    winemag-data-130k-v2.csv
  sources.json
output/
  analiza_danych_i_pytania_badawcze.pdf
  figures/
  tables/
```

PDF jest gotowym, stałym raportem. Notebook przelicza analizę i zapisuje wykresy PNG oraz tabele CSV;
nie tworzy ponownie PDF. `data/sources.json` zawiera adresy źródłowe i sumy kontrolne plików.

## Zakres analizy

- Braki danych, powtórzenia, statystyki opisowe i obserwacje odstające według reguły IQR.
- Rozkład ocen i korelacje Spearmana osobno dla win czerwonych i białych.
- Rozkłady ocen i długości recenzji oraz zależności ceny i długości opisu od oceny.
- Porównanie częstości słów w grupach `points >= 90` i `points <= 85`.
- Cztery pytania badawcze z hipotezami i planem weryfikacji.

Po usunięciu powtórzeń pozostaje 1359 czerwonych i 3961 białych win oraz 119954 recenzji.
Cena jest dostępna dla 111566 oczyszczonych recenzji. Nie uzupełniamy brakujących cen ani nie usuwamy
automatycznie obserwacji odstających. Przy powtórzeniach zachowujemy pierwsze wystąpienie;
dla opisów normalizujemy wielkość liter i białe znaki.

Zbiory dotyczą różnych win i używają różnych skal ocen, dlatego nie łączymy rekordów.
Korelacje i różnice słownictwa opisują tę próbę, a nie zależności przyczynowe.

## Źródła

- [UCI Wine Quality](https://archive.ics.uci.edu/dataset/186/wine%2Bquality), Cortez i in. (2009).
  [DOI: 10.24432/C56S3T](https://doi.org/10.24432/C56S3T), licencja **CC BY 4.0**.
  Pliki czerwonych i białych win pochodzą z tego samego zasobu.
- [Wine Reviews](https://www.kaggle.com/datasets/zynicide/wine-reviews), Zack Thoutt;
  opisy degustacyjne Wine Enthusiast, plik `winemag-data-130k-v2.csv`, licencja **CC BY-NC-SA 4.0**.