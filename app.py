"""Przeglądarka wyników projektu (Gradio): dane liczbowe, recenzje, tabele i wykresy z analizy.

Uruchomienie:  python app.py   (potem otwórz adres wypisany w terminalu, zwykle http://127.0.0.1:7860)
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
TABLES = ROOT / "output" / "tables"
FIGURES = ROOT / "output" / "figures"

TYPES = {"red": "Czerwone", "white": "Białe"}
LABELS = {
    "fixed acidity": "Kwasowość stała", "volatile acidity": "Kwasowość lotna",
    "citric acid": "Kwas cytrynowy", "residual sugar": "Cukier resztkowy",
    "chlorides": "Chlorki", "free sulfur dioxide": "Wolny SO₂",
    "total sulfur dioxide": "Całkowity SO₂", "density": "Gęstość", "pH": "pH",
    "sulphates": "Siarczany", "alcohol": "Alkohol",
}
ALL = "Wszystkie"


# ---------------------------------------------------------------- dane
@lru_cache(maxsize=1)
def load_wines() -> dict[str, pd.DataFrame]:
    """Dane liczbowe po usunięciu powtórzeń (jak w notebooku)."""
    return {
        kind: pd.read_csv(RAW / f"winequality-{kind}.csv", sep=";").drop_duplicates().reset_index(drop=True)
        for kind in TYPES
    }


@lru_cache(maxsize=1)
def load_reviews() -> pd.DataFrame:
    """Recenzje po czyszczeniu: bez indeksu CSV, powtórzeń wierszy i powtórzonych opisów."""
    frame = pd.read_csv(RAW / "winemag-data-130k-v2.csv", index_col=0).drop_duplicates()
    key = frame.description.str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    frame = frame.loc[~key.duplicated()].reset_index(drop=True)
    frame["word_count"] = frame.description.str.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?").str.len()
    return frame


# ---------------------------------------------------------------- dane liczbowe
def numeric_summary(kind: str) -> tuple[pd.DataFrame, str]:
    frame = load_wines()[kind]
    table = frame.drop(columns="quality").describe().T.round(3)
    table.index = [LABELS[c] for c in table.index]
    info = (f"{TYPES[kind]}: {len(frame)} win po usunięciu powtórzeń. "
            f"Średnia ocena quality: {frame.quality.mean():.2f}, mediana: {frame.quality.median():.0f}.")
    return table.reset_index(names="cecha"), info


def feature_plot(kind: str, feature_label: str):
    inverse = {v: k for k, v in LABELS.items()}
    feature = inverse[feature_label]
    frame = load_wines()[kind]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    axes[0].hist(frame[feature], bins=30, color="#8c5a6b", alpha=0.8)
    axes[0].set_title(f"Rozkład: {feature_label}")
    levels = sorted(frame.quality.unique())
    axes[1].boxplot([frame.loc[frame.quality == q, feature] for q in levels],
                    tick_labels=levels, patch_artist=True,
                    boxprops={"facecolor": "#5f9ea0", "alpha": 0.55}, medianprops={"color": "black"},
                    flierprops={"markersize": 2})
    axes[1].set_xlabel("quality")
    axes[1].set_title(f"{feature_label} a ocena")
    fig.tight_layout()
    return fig


def quality_correlations(kind: str) -> pd.DataFrame:
    frame = load_wines()[kind]
    corr = frame.drop(columns="quality").corrwith(frame.quality, method="spearman").sort_values(key=abs, ascending=False)
    return pd.DataFrame({"cecha": [LABELS[c] for c in corr.index], "rho Spearmana z quality": corr.round(3).values})


# ---------------------------------------------------------------- recenzje
def review_choices() -> tuple[list[str], list[str]]:
    reviews = load_reviews()
    countries = [ALL] + reviews.country.value_counts().head(25).index.tolist()
    varieties = [ALL] + reviews.variety.value_counts().head(40).index.tolist()
    return countries, varieties


def filter_reviews(country: str, variety: str, points_range: tuple[float, float], only_priced: bool) -> pd.DataFrame:
    reviews = load_reviews()
    mask = reviews.points.between(points_range[0], points_range[1])
    if country != ALL:
        mask &= reviews.country == country
    if variety != ALL:
        mask &= reviews.variety == variety
    if only_priced:
        mask &= reviews.price.notna()
    return reviews[mask]


def review_explorer(country: str, variety: str, points_min: float, points_max: float, only_priced: bool, n: int):
    sub = filter_reviews(country, variety, (points_min, points_max), only_priced)
    if sub.empty:
        return "Brak recenzji dla tych filtrów.", pd.DataFrame(), plt.figure(figsize=(4, 2))
    count = f"{len(sub):,}".replace(",", " ")
    median_price = "brak" if sub.price.notna().sum() == 0 else f"{sub.price.median():.0f}"
    stats_line = (f"Recenzji: {count}. Średnia ocena: {sub.points.mean():.2f}, mediana ceny: "
                  f"{median_price}, średnia liczba słów w opisie: {sub.word_count.mean():.1f}.")
    sample = sub.sample(min(int(n), len(sub)), random_state=0)[
        ["title", "country", "variety", "points", "price", "description"]]
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    ax.hist(sub.points, bins=np.arange(79.5, 101.5, 1), color="#5f9ea0", alpha=0.85)
    ax.set_xlabel("points")
    ax.set_ylabel("liczba recenzji")
    fig.tight_layout()
    return stats_line, sample, fig


def top_words(country: str, variety: str, points_min: float, points_max: float, top: int = 15) -> pd.DataFrame:
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

    sub = filter_reviews(country, variety, (points_min, points_max), False)
    stop = set(ENGLISH_STOP_WORDS) | {"wine", "wines"}
    counts: dict[str, int] = {}
    for text in sub.description.head(20000):
        for word in set(re.findall(r"[a-z]{3,}", text.lower())):
            if word not in stop:
                counts[word] = counts.get(word, 0) + 1
    total = max(1, min(len(sub), 20000))
    rows = sorted(counts.items(), key=lambda kv: -kv[1])[: int(top)]
    return pd.DataFrame({"słowo": [w for w, _ in rows], "odsetek recenzji (%)": [round(100 * c / total, 1) for _, c in rows]})


# ---------------------------------------------------------------- tabele i wykresy z analizy
def table_names() -> list[str]:
    return sorted(p.stem for p in TABLES.glob("*.csv"))


def read_table(name: str) -> pd.DataFrame:
    return pd.read_csv(TABLES / f"{name}.csv", encoding="utf-8-sig")


def figure_files() -> list[str]:
    return [str(p) for p in sorted(FIGURES.glob("*.png"))]


# ---------------------------------------------------------------- interfejs
def build_ui():
    import gradio as gr

    countries, varieties = review_choices()
    with gr.Blocks(title="Jakość wina - przeglądarka wyników") as demo:
        gr.Markdown("# Jakość wina: przeglądarka wyników etapu 1\n"
                    "Dane liczbowe (UCI Wine Quality) i tekstowe (Wine Reviews). Pełna analiza: `analiza_wina.ipynb`.")

        with gr.Tab("Dane liczbowe"):
            with gr.Row():
                kind = gr.Radio([("Czerwone", "red"), ("Białe", "white")], value="red", label="Typ wina")
                feature = gr.Dropdown(list(LABELS.values()), value="Alkohol", label="Cecha")
            info = gr.Markdown()
            plot = gr.Plot()
            with gr.Row():
                summary = gr.Dataframe(label="Statystyki opisowe", interactive=False)
                corr = gr.Dataframe(label="Korelacja z quality", interactive=False)

            def refresh_numeric(k, f):
                table, text = numeric_summary(k)
                return text, feature_plot(k, f), table, quality_correlations(k)

            for control in (kind, feature):
                control.change(refresh_numeric, [kind, feature], [info, plot, summary, corr])
            demo.load(refresh_numeric, [kind, feature], [info, plot, summary, corr])

        with gr.Tab("Recenzje"):
            with gr.Row():
                country = gr.Dropdown(countries, value=ALL, label="Kraj")
                variety = gr.Dropdown(varieties, value=ALL, label="Odmiana")
            with gr.Row():
                pmin = gr.Slider(80, 100, value=80, step=1, label="Ocena od")
                pmax = gr.Slider(80, 100, value=100, step=1, label="Ocena do")
                priced = gr.Checkbox(value=False, label="Tylko z ceną")
                n = gr.Slider(1, 50, value=10, step=1, label="Liczba przykładowych recenzji")
            go = gr.Button("Pokaż")
            line = gr.Markdown()
            hist = gr.Plot()
            sample = gr.Dataframe(label="Losowa próbka recenzji", interactive=False, wrap=True)
            words = gr.Dataframe(label="Najczęstsze słowa w wybranej grupie", interactive=False)
            go.click(review_explorer, [country, variety, pmin, pmax, priced, n], [line, sample, hist])
            go.click(top_words, [country, variety, pmin, pmax], [words])

        with gr.Tab("Tabele z analizy"):
            name = gr.Dropdown(table_names(), label="Tabela (output/tables)")
            table = gr.Dataframe(interactive=False)
            name.change(read_table, name, table)

        with gr.Tab("Wykresy"):
            gr.Gallery(value=figure_files(), label="output/figures", columns=2, height="auto")
    return demo


if __name__ == "__main__":
    build_ui().launch()
