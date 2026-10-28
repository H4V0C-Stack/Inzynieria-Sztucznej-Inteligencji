"""Generuje raport PDF etapu 1: output/analiza_danych_i_pytania_badawcze.pdf

Użycie:
    python report/build_report.py
    python report/build_report.py --repo https://github.com/ORG/NAZWA
Skład zespołu i adres repozytorium: report/team.json. Tabele i wykresy: output/tables, output/figures
(najpierw uruchom notebook analiza_wina.ipynb).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import pandas as pd
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "output" / "tables"
FIGURES = ROOT / "output" / "figures"
OUT = ROOT / "output" / "analiza_danych_i_pytania_badawcze.pdf"

# ------------------------------------------------------------------ czcionki (DejaVu z pakietu matplotlib)
FONT_DIR = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
pdfmetrics.registerFont(TTFont("DV", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DV-B", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DV-I", str(FONT_DIR / "DejaVuSans-Oblique.ttf")))
pdfmetrics.registerFont(TTFont("DV-BI", str(FONT_DIR / "DejaVuSans-BoldOblique.ttf")))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")

ACCENT = colors.HexColor("#7a3b4e")
GRID = colors.HexColor("#c9c9c9")
HEAD_BG = colors.HexColor("#efe3e6")

BODY = ParagraphStyle("body", fontName="DV", fontSize=9, leading=13, alignment=TA_JUSTIFY, spaceAfter=5)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=7.5, leading=10, alignment=0, spaceAfter=0)
CELL = ParagraphStyle("cell", parent=SMALL, fontSize=7.2, leading=9)
CELLB = ParagraphStyle("cellb", parent=CELL, fontName="DV-B")
CAPTION = ParagraphStyle("caption", parent=SMALL, fontName="DV-I", textColor=colors.HexColor("#444444"),
                         spaceBefore=2, spaceAfter=8)
H1 = ParagraphStyle("h1", fontName="DV-B", fontSize=13.5, leading=17, textColor=ACCENT, spaceBefore=12, spaceAfter=6, keepWithNext=1)
H2 = ParagraphStyle("h2", fontName="DV-B", fontSize=10.5, leading=14, textColor=ACCENT, spaceBefore=8, spaceAfter=4, keepWithNext=1)
TITLE = ParagraphStyle("title", fontName="DV-B", fontSize=19, leading=24, textColor=ACCENT, spaceAfter=4)
SUB = ParagraphStyle("sub", fontName="DV", fontSize=10.5, leading=15, spaceAfter=3)
BUL = ParagraphStyle("bul", parent=BODY, leftIndent=12, bulletIndent=2, spaceAfter=2)

FRAME_W = A4[0] - 4 * cm


def P(text, style=BODY):
    return Paragraph(text, style)


def bullets(items):
    return [Paragraph(t, BUL, bulletText="•") for t in items]


def fmt(v, digits=3):
    if isinstance(v, float):
        if v != v:
            return ""
        if abs(v) >= 1000 or float(v).is_integer():
            return f"{v:,.0f}".replace(",", " ")
        return f"{v:.{digits}f}"
    if isinstance(v, int):
        return f"{v:,}".replace(",", " ")
    return str(v)


def table(frame: pd.DataFrame, col_widths=None, digits=3, header=None, align_first_left=True):
    header = header or list(frame.columns)
    data = [[Paragraph(str(h), CELLB) for h in header]]
    for _, row in frame.iterrows():
        data.append([Paragraph(fmt(v, digits), CELL) for v in row])
    if col_widths is None:
        col_widths = [FRAME_W / len(header)] * len(header)
    else:
        total = sum(col_widths)
        col_widths = [w / total * FRAME_W for w in col_widths]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    return t


def figure(name: str, caption: str, width_frac=1.0):
    path = FIGURES / f"{name}.png"
    w, h = PILImage.open(path).size
    width = FRAME_W * width_frac
    img = Image(str(path), width=width, height=width * h / w)
    return KeepTogether([img, P(caption, CAPTION)])


def read(name: str) -> pd.DataFrame:
    return pd.read_csv(TABLES / f"{name}.csv", encoding="utf-8-sig")


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("DV", 7.5)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(2 * cm, 1.2 * cm, "Uczenie maszynowe – Projekt 1, etap 1: Jakość wina – analiza danych i pytania badawcze")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Strona {doc.page}")
    canvas.restoreState()


# ------------------------------------------------------------------ treść
def build(repo_url: str, team: list[dict]):
    story = []

    story += [P("Jakość wina: analiza danych i pytania badawcze", TITLE),
              P("Uczenie maszynowe – Projekt 1, etap 1 (zima 2026)", SUB),
              P("Termin: 30.10.2026, 23:59 (Platon, zakładka „projekt”)", SUB), Spacer(1, 6)]

    # 1. Zespół ---------------------------------------------------------------------------
    story.append(P("1. Informacja o zespole", H1))
    rows = pd.DataFrame([{"Nazwisko i imię": m["name"], "Numer ID": m["id"], "Zakres pracy": m["role"]} for m in team])
    story.append(table(rows, col_widths=[3.2, 1.6, 9]))
    story.append(Spacer(1, 6))
    if "WSTAW" in repo_url:
        link = "<font color='#b00020'><b>[WSTAW LINK DO REPOZYTORIUM – report/team.json lub parametr --repo]</b></font>"
    else:
        link = f"<link href='{repo_url}' color='blue'>{repo_url}</link>"
    story.append(P(f"<b>Repozytorium GitHub (kod, dane, raporty, README):</b> {link}"))

    # 2. Dane -----------------------------------------------------------------------------
    story.append(P("2. Informacja o danych", H1))
    story.append(P(
        "Projekt wykorzystuje dwa publicznie dostępne, rzeczywiste (nie symulowane ani syntetyczne) zbiory danych o winach: "
        "liczbowy zbiór pomiarów fizykochemicznych oraz tekstowy zbiór opisów degustacyjnych. Zbiory dotyczą różnych win "
        "i mają różne skale ocen, dlatego nie łączymy rekordów; łączy je wspólne pytanie badawcze o to, jakie informacje "
        "o ocenianej jakości wina niosą pomiary, a jakie opisy tekstowe (sekcja 4)."))

    story.append(P("2.1 Zbiór 1 – dane liczbowe: UCI Wine Quality", H2))
    story += bullets([
        "<b>Źródło:</b> UCI Machine Learning Repository, <link href='https://archive.ics.uci.edu/dataset/186/wine%2Bquality' "
        "color='blue'>archive.ics.uci.edu/dataset/186/wine+quality</link>; Cortez, Cerdeira, Almeida, Matos, Reis (2009), "
        "DOI: 10.24432/C56S3T; licencja CC BY 4.0.",
        "<b>Pliki:</b> winequality-red.csv (1\u00a0599 wierszy), winequality-white.csv (4\u00a0898 wierszy), winequality.names (opis); "
        "separator „;”, 12 kolumn: 11 cech fizykochemicznych i <i>quality</i>. Pobrano 23.10.2026.",
        "<b>Charakter danych:</b> pomiary laboratoryjne i ocena sensoryczna (skala 0–10) win „vinho verde” z północnej Portugalii. "
        "Ocena <i>quality</i> jest porządkowa. Nie ma braków danych.",
        "<b>Cechy:</b> kwasowość stała, kwasowość lotna, kwas cytrynowy, cukier resztkowy, chlorki, wolny i całkowity SO₂, "
        "gęstość, pH, siarczany, alkohol.",
    ])
    story.append(P("2.2 Zbiór 2 – dane w języku naturalnym: Wine Reviews", H2))
    story += bullets([
        "<b>Źródło:</b> Kaggle, <link href='https://www.kaggle.com/datasets/zynicide/wine-reviews' color='blue'>"
        "kaggle.com/datasets/zynicide/wine-reviews</link> (Zack Thoutt); opisy degustacyjne ze strony Wine Enthusiast; "
        "plik winemag-data-130k-v2.csv; licencja CC BY-NC-SA 4.0. Pobrano 23.10.2026.",
        "<b>Rozmiar:</b> 129\u00a0971 recenzji, 13 kolumn danych (plus kolumna indeksu): kraj, opis (<i>description</i>), oznaczenie, "
        "ocena <i>points</i> (80–100), cena, prowincja, regiony, autor recenzji, tytuł, odmiana, winnica.",
        "<b>Dane tekstowe:</b> kolumna <i>description</i> (angielskie opisy degustacyjne, mediana 40 słów). "
        "Cena i metadane są danymi uzupełniającymi.",
    ])
    story.append(P("2.3 Podzbiory i sposób ich otrzymania", H2))
    story.append(P(
        "Nie używamy próbkowania ani podzbiorów losowych: analizujemy pełne pliki. Jedyne przekształcenia to czyszczenie "
        "opisane poniżej; wykonuje je kod w <i>analiza_wina.ipynb</i> (sekcje 1 i 2) i <i>app.py</i>. Surowe pliki są też w "
        "repozytorium w <i>data/raw</i>, a adresy źródłowe, daty pobrania i sumy kontrolne w <i>data/sources.json</i>. "
        "Plik z Kaggle wymaga zalogowania przy pobieraniu ze strony; kopia w repozytorium pozwala odtworzyć wyniki bez pobierania."))
    clean = pd.DataFrame([
        ["Wina czerwone", "1 599", "1 359", "usunięto 240 powtórzonych wierszy"],
        ["Wina białe", "4 898", "3 961", "usunięto 937 powtórzonych wierszy"],
        ["Recenzje", "129 971", "119 954",
         "bez kolumny indeksu, bez powtórzonych wierszy (-9 983) i powtórzonych opisów (-34, po normalizacji wielkości liter i spacji); "
         "pierwsze wystąpienie zostaje"],
    ], columns=["Zbiór", "Wiersze surowe", "Po czyszczeniu", "Reguła"])
    story.append(table(clean, col_widths=[2.2, 2, 2, 8]))
    story.append(P("Brakujących cen (ok. 7% recenzji) nie uzupełniamy, a obserwacji odstających nie usuwamy.", CAPTION))

    # 3. EDA ------------------------------------------------------------------------------
    story.append(P("3. Analiza eksploracyjna danych (EDA)", H1))
    story.append(P("3.1 Dane liczbowe (UCI Wine Quality)", H2))
    ov = read("numeric_overview")
    ov.columns = ["Miara", "Czerwone", "Białe"]
    story.append(table(ov, col_widths=[5, 2, 2], digits=2))
    story.append(Spacer(1, 4))
    story.append(P(
        "Oceny 5 i 6 dominują (82% win czerwonych i 75% białych), a oceny skrajne są rzadkie, dlatego rozkład jest silnie "
        "skoncentrowany. Białe wina mają nieco wyższą średnią ocenę (5,85 wobec 5,62)."))
    story.append(figure("01_quality_distribution", "Rysunek 1. Rozkład ocen quality w winach czerwonych i białych (udział w danym typie)."))

    out = read("iqr_outliers")
    out.columns = ["Cecha", "Czerwone", "Białe"]
    out["Cecha"] = [
        "kwasowość stała", "kwasowość lotna", "kwas cytrynowy", "cukier resztkowy", "chlorki", "wolny SO₂",
        "całkowity SO₂", "gęstość", "pH", "siarczany", "alkohol"]
    story.append(P("Obserwacje odstające wg reguły IQR (1,5·IQR) to liczba wartości poza wąsami; nie usuwamy ich, bo mogą "
                   "opisywać prawdziwe, nietypowe wina.", BODY))
    story.append(table(out, col_widths=[4, 2, 2]))
    story.append(Spacer(1, 6))
    story.append(figure("07_feature_distributions",
                        "Rysunek 2. Rozkłady cech fizykochemicznych: czerwone i białe wina. Cechy są w większości prawoskośne; "
                        "białe i czerwone różnią się położeniem i rozrzutem.", width_frac=0.9))
    story.append(P(
        "Test D’Agostino–Pearsona odrzuca normalność rozkładu praktycznie dla wszystkich cech (p &lt; 0,001, najczęściej "
        "znacznie mniej), a największą skośność mają chlorki (≈5) i cukier resztkowy w winach czerwonych (≈4,5). Dlatego "
        "stosujemy testy rangowe. Pełna tabela: <i>output/tables/normality_tests.csv</i>."))
    story.append(figure("02_correlations", "Rysunek 3. Korelacje Spearmana cech fizykochemicznych z oceną quality (osobno dla typów wina)."))
    story.append(figure("03_alcohol_quality", "Rysunek 4. Zawartość alkoholu w grupach ocen quality."))
    story.append(figure("08_feature_correlations",
                        "Rysunek 5. Korelacje Spearmana między cechami (wielokolinearność)."))
    pairs = read("feature_correlation_pairs")
    pairs.columns = ["Typ", "Cecha 1", "Cecha 2", "ρ"]
    story.append(P("Najsilniejsze zależności między cechami (|ρ| ≥ 0,6):", BODY))
    story.append(table(pairs, col_widths=[2, 3.2, 3.2, 1.4]))

    story.append(P("3.2 Dane tekstowe (Wine Reviews)", H2))
    story.append(P(
        "Po czyszczeniu pozostaje 119\u00a0954 recenzji, z czego 111\u00a0566 ma cenę. Ocena <i>points</i> ma średnią 88,4 i medianę 88, "
        "a opis ma medianę 40 słów. W surowym pliku (129\u00a0971 recenzji) najczęściej brakuje drugiego regionu (61%), "
        "oznaczenia (29%), danych autora recenzji (24% w polu Twittera, 20% w nazwisku) i pierwszego regionu (16%); "
        "brak ceny dotyczy 6,9% recenzji. Tabela poniżej pokazuje braki w surowym pliku."))
    miss = read("reviews_missing")
    miss.columns = ["Kolumna", "Braki (n)", "Braki (%)"]
    story.append(table(miss.head(8), col_widths=[4, 2, 2], digits=1))
    story.append(Spacer(1, 4))
    desc = read("reviews_describe")
    desc.columns = ["Miara", "points", "price", "word_count", "char_count"]
    story.append(table(desc, col_widths=[1.5, 1.6, 1.6, 1.6, 1.6], digits=1))
    story.append(Spacer(1, 4))
    story.append(figure("04_reviews_distribution", "Rysunek 6. Rozkład ocen points oraz liczby słów w recenzji."))
    story.append(figure("05_price_length",
                        "Rysunek 7. Cena (skala logarytmiczna) a ocena oraz mediana liczby słów opisu w zależności od oceny."))
    story.append(P(
        "Najliczniejsze kraje to USA (50\u00a0447 recenzji), Francja (20\u00a0351), Włochy (17\u00a0921), Hiszpania (6\u00a0116) i Portugalia (5\u00a0256); "
        "najczęstsze odmiany to Pinot Noir (12\u00a0277), Chardonnay (10\u00a0867) i Cabernet Sauvignon (8\u00a0837)."))
    story.append(figure("09_points_by_country", "Rysunek 8. Rozkład ocen points w ośmiu najliczniejszych krajach."))
    story.append(figure("06_words",
                        "Rysunek 9. Słowa, których odsetek recenzji różni się najbardziej między grupami points ≥ 90 i points ≤ 85 "
                        "(różnica w punktach procentowych). Opis bez kontroli długości, odmiany i autora."))

    # 3.3 testy ----------------------------------------------------------------------------
    story.append(P("3.3 Testy statystyczne", H2))
    story.append(P(
        "Ponieważ rozkłady nie są normalne, a <i>quality</i> i <i>points</i> są oceniami porządkowymi, stosujemy testy rangowe. "
        "Do każdego wyniku podajemy wielkość efektu, a przy wielu porównaniach korektę Bonferroniego, bo przy tak dużych "
        "próbach bardzo niskie p nie oznacza dużego efektu."))
    mw = read("test_mann_whitney_red_white")
    mw = mw[["cecha", "mediana_czerwone", "mediana_biale", "efekt_r", "p_Bonferroni"]]
    mw.columns = ["Cecha", "Mediana czerwone", "Mediana białe", "Efekt r", "p (Bonferroni)"]
    story.append(P("<b>Mann–Whitney: wina czerwone vs białe</b> (efekt r = rank-biserial, od −1 do 1). Największe różnice dotyczą "
                   "całkowitego SO₂, chlorków i kwasowości lotnej; różnica w ocenie quality jest mała (|r| ≈ 0,15).", BODY))
    story.append(table(mw, col_widths=[3.2, 2.2, 2.2, 1.6, 2.2]))
    story.append(Spacer(1, 6))

    sp = read("spearman_quality_ci")
    wide = []
    for cecha, g in sp.groupby("cecha", sort=False):
        row = {"Cecha": cecha}
        for typ in ("Czerwone", "Białe"):
            r = g[g.typ == typ].iloc[0]
            mark = "" if bool(r.istotna_po_korekcie) else " (n.i.)"
            row[typ] = f"{r.rho:.2f} [{r.CI95_dol:.2f}; {r.CI95_gora:.2f}]{mark}"
        wide.append(row)
    story.append(P("<b>Korelacje Spearmana z quality</b> z 95% przedziałem ufności (przybliżenie Fieller’a); „n.i.” oznacza brak "
                   "istotności po korekcie Bonferroniego (22 porównania). Najsilniejsza jest dodatnia zależność z alkoholem "
                   "(ρ ≈ 0,48 w obu typach).", BODY))
    story.append(table(pd.DataFrame(wide), col_widths=[3.2, 4, 4]))
    story.append(Spacer(1, 6))

    kw = read("kruskal_alcohol_quality")
    kw.columns = ["Typ", "Liczba grup", "H", "p", "ε²"]
    story.append(P("<b>Kruskal–Wallis: zawartość alkoholu w grupach jakości</b> (grupy z n ≥ 5). Różnice są duże (ε² ≈ 0,24–0,27), "
                   "co zgadza się z korelacjami; to związek opisowy, nie przyczynowy.", BODY))
    story.append(table(kw, col_widths=[2, 2, 2, 2, 2], digits=2))
    story.append(Spacer(1, 6))

    kg = read("kruskal_points_groups")
    kg.columns = ["Grupowanie", "H", "p", "ε²"]
    kg["Grupowanie"] = kg["Grupowanie"].map({"country": "kraj (5 największych)", "variety": "odmiana (5 największych)",
                                             "taster_name": "autor recenzji (5 najliczniejszych)"})
    story.append(P("<b>Kruskal–Wallis: oceny points w grupach.</b> Efekt jest największy dla autora recenzji (ε² ≈ 0,07), "
                   "a dla odmiany i kraju mały; modele tekstowe warto więc oceniać z podziałem uwzględniającym autora.", BODY))
    story.append(table(kg, col_widths=[4, 2, 2, 2], digits=3))
    story.append(Spacer(1, 6))

    rv = read("spearman_reviews_ci")
    rv.columns = ["Zależność", "n", "ρ", "CI95 dół", "CI95 góra", "p"]
    story.append(P("<b>Recenzje: ρ Spearmana</b> – cena i długość opisu a ocena. Długość opisu rośnie z oceną; w porównaniu grup "
                   "points ≥ 90 i ≤ 85 opisy wyżej ocenianych są dłuższe (Mann–Whitney, efekt r ≈ 0,68).", BODY))
    story.append(table(rv, col_widths=[3, 1.8, 1.4, 1.6, 1.6, 1.6]))
    story.append(Spacer(1, 6))
    wc = read("word_chi2_tests")
    wc.columns = ["Słowo", "Różnica (p.p.)", "χ²", "p (Bonferroni)"]
    story.append(P("<b>Słownictwo: test χ²</b> dla obecności słowa w grupach points ≥ 90 i ≤ 85 (pięć słów w każdą stronę, korekta "
                   "Bonferroniego na wszystkie słowa). Różnice są istotne, ale opisują wzorce w tekstach, a nie przyczynę oceny.", BODY))
    story.append(table(wc, col_widths=[2.5, 2.5, 2.5, 3], digits=1))

    # 4. Pytania ---------------------------------------------------------------------------
    story.append(P("4. Pytania badawcze", H1))
    story.append(P("<b>Pytanie główne:</b> Jakie informacje o ocenianej jakości wina zawierają pomiary fizykochemiczne i opisy "
                   "degustacyjne oraz jakie wzorce można rozpoznać w każdym z tych źródeł?"))
    qs = [
        ("1", "Które cechy fizykochemiczne najsilniej wiążą się z oceną jakości i czy zależności różnią się między winami czerwonymi a białymi?",
         "Dodatnia zależność alkoholu występuje w obu typach, a znaczenie pozostałych cech jest różne (potwierdzone wstępnie: "
         "alkohol ρ ≈ 0,48; kwasowość lotna i siarczany ważne dla czerwonych, chlorki i gęstość dla białych).",
         "Etap 2: regresja liniowa/Ridge i random forest, baza medianowa; MAE, RMSE."),
        ("2", "Czy treść opisu degustacyjnego pozwala przewidywać ocenę lepiej niż sama długość recenzji?",
         "Treść wnosi dodatkową informację poza długością (długość ma ρ ≈ 0,5 z oceną).",
         "Etap 2–3: baza medianowa, model długości, TF-IDF + Ridge, embeddingi transformera + regresja; ten sam podział i metryki. "
         "Wejściem jest wyłącznie <i>description</i>."),
        ("3", "Czy dodatnia zależność ceny od oceny występuje także w obrębie porównywalnych grup win?",
         "Kierunek jest dodatni również wewnątrz popularnych odmian (wstępnie ρ ≈ 0,55–0,69 w pięciu największych).",
         "Spearman i mediany w grupach n ≥ 100, następnie kontrola kraju i autora oraz raportowanie braków cen."),
        ("4", "Czy bez użycia ocen można odkryć grupy win lub opisów, które różnią się później rozkładem ocen?",
         "Istnieją interpretowalne grupy o różnych profilach i ocenach.",
         "K-means i klasteryzacja hierarchiczna osobno dla cech chemicznych i reprezentacji tekstu; silhouette, stabilność, "
         "interpretowalność; oceny porównujemy dopiero po ustaleniu grup."),
    ]
    for num, q, hyp, method in qs:
        story.append(KeepTogether([
            P(f"<b>Pytanie {num}.</b> {q}", BODY),
            P(f"<i>Hipoteza:</i> {hyp}", BODY),
            P(f"<i>Metody:</i> {method}", BODY),
        ]))
    plan = pd.DataFrame([
        ["Metody nadzorowane (2)", "Ridge i random forest (dane liczbowe); TF-IDF + Ridge (tekst)", "P1, P2"],
        ["Metody nienadzorowane (2)", "K-means i klasteryzacja hierarchiczna", "P4"],
        ["Modele NLP", "TF-IDF i model długości jako punkt odniesienia", "P2"],
        ["Modele transformerowe", "Embeddingi zdań/opisów + regresja", "P2, P4"],
        ["Interfejs", "Gradio (app.py): EDA i wyniki", "wszystkie"],
    ], columns=["Wymaganie projektu", "Planowane użycie", "Pytania"])
    story.append(P("Powiązanie z wymaganiami kolejnych etapów projektu:", BODY))
    story.append(table(plan, col_widths=[3.4, 7, 1.6]))
    story.append(Spacer(1, 6))
    story.append(P("Hipotezy powstały po obejrzeniu całej próby i są eksploracyjne. Zbiory nie są reprezentatywne dla rynku wina, "
                   "korelacje opisują próbę, a nie związki przyczynowe. Przed modelowaniem ustalimy podział danych (z grupowaniem "
                   "rekordów tego samego wina), a preprocessing dopasujemy tylko na zbiorze treningowym.", BODY))

    # 5. Repozytorium ----------------------------------------------------------------------
    story.append(P("5. Repozytorium i odtworzenie wyników", H1))
    story.append(P(f"<b>Link do repozytorium:</b> {link}"))
    story += bullets([
        "<b>Kod:</b> <i>analiza_wina.ipynb</i> (EDA, testy, pytania), <i>app.py</i> (interfejs Gradio), <i>report/build_report.py</i>.",
        "<b>Dane:</b> <i>data/raw</i> (4 pliki), <i>data/sources.json</i> (źródła, sumy kontrolne).",
        "<b>Wyniki:</b> <i>output/figures</i> (wykresy PNG), <i>output/tables</i> (tabele CSV), niniejszy raport PDF.",
        "<b>Odtworzenie:</b> <i>pip install -r requirements.txt</i>, uruchomienie notebooka od góry do dołu, "
        "<i>python app.py</i> – przeglądarka wyników w Gradio (zakładki: dane liczbowe, recenzje, tabele, wykresy).",
    ])

    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                            bottomMargin=2 * cm, title="Jakość wina – analiza danych i pytania badawcze",
                            author="Zespół projektu ML (Uczenie maszynowe, zima 2026)")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print("OK:", OUT)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", help="adres repozytorium GitHub (nadpisuje report/team.json)")
    args = ap.parse_args()
    cfg = json.loads((Path(__file__).parent / "team.json").read_text(encoding="utf-8"))
    build(args.repo or cfg["repo_url"], cfg["team"])
