from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.data import GOLD_TABLES, available_run_ids, filter_by_runs_and_strategies, load_gold_table


DATA_DIR = Path("data")


def main() -> None:
    st.set_page_config(page_title="Prisoners Dilemma Dashboard", layout="wide")
    st.title("Prisoners Dilemma Dashboard")

    run_ids = available_run_ids(DATA_DIR)
    if not run_ids:
        st.warning("Aucune donnee trouvee. Lance `make run` pour generer Bronze, Silver et Gold.")
        return

    tables = {table: load_gold_table(DATA_DIR, table) for table in GOLD_TABLES}
    selected_runs = st.sidebar.multiselect("Runs", run_ids, default=[run_ids[-1]])
    strategy_options = sorted(
        str(strategy)
        for strategy in tables["tournament_summary"]
        .get("strategy_name", pd.Series(dtype=str))
        .dropna()
        .unique()
    )
    selected_strategies = st.sidebar.multiselect(
        "Strategies",
        strategy_options,
        default=strategy_options,
    )

    if not selected_runs:
        st.info("Selectionne au moins un run.")
        return
    if not selected_strategies:
        st.info("Selectionne au moins une strategie.")
        return

    filtered = {
        name: filter_by_runs_and_strategies(table, selected_runs, selected_strategies)
        for name, table in tables.items()
    }

    render_metrics(filtered["tournament_summary"], selected_runs)
    render_ranking(filtered["tournament_summary"])
    render_matchup_heatmap(filtered["matchup_matrix"], selected_runs)
    render_behavioral_drift(filtered["behavioral_drift"])
    render_forgiveness(filtered["forgiveness_index"])
    render_run_comparison(filtered["run_comparison"])
    render_tables(filtered)


def render_metrics(summary: pd.DataFrame, selected_runs: list[str]) -> None:
    st.subheader("Vue generale")
    if summary.empty:
        st.info("Aucun resume disponible pour les filtres selectionnes.")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Runs", len(selected_runs))
    col2.metric("Strategies", summary["strategy_name"].nunique())
    col3.metric("Score total moyen", f"{summary['total_score'].mean():.1f}")
    col4.metric("Cooperation moyenne", f"{summary['cooperation_rate'].mean():.1%}")


def render_ranking(summary: pd.DataFrame) -> None:
    st.subheader("Classement des strategies")
    if summary.empty:
        st.info("Aucun classement disponible.")
        return

    fig = px.bar(
        summary.sort_values(["run_id", "rank"]),
        x="strategy_name",
        y="total_score",
        color="strategy_type",
        facet_col="run_id" if summary["run_id"].nunique() > 1 else None,
        hover_data=["avg_score_per_round", "cooperation_rate", "wins", "losses", "draws"],
        labels={"strategy_name": "Strategie", "total_score": "Score total"},
    )
    fig.update_layout(xaxis_tickangle=-35, legend_title_text="Type")
    st.plotly_chart(fig, use_container_width=True)


def render_matchup_heatmap(matchups: pd.DataFrame, selected_runs: list[str]) -> None:
    st.subheader("Matrice des confrontations")
    if matchups.empty:
        st.info("Aucune matrice de confrontation disponible.")
        return

    run_for_heatmap = selected_runs[-1]
    frame = matchups[matchups["run_id"] == run_for_heatmap]
    if frame.empty:
        st.info("Aucune confrontation disponible pour le run affiche.")
        return

    pivot = frame.pivot_table(
        index="strategy_a",
        columns="strategy_b",
        values="avg_score_a",
        aggfunc="mean",
    )
    if pivot.empty:
        st.info("Aucune matrice exploitable pour les filtres selectionnes.")
        return

    fig = px.imshow(
        pivot,
        text_auto=".1f",
        aspect="auto",
        color_continuous_scale="Viridis",
        labels={"color": "Score moyen A"},
    )
    st.caption(f"Run affiche: {run_for_heatmap}")
    st.plotly_chart(fig, use_container_width=True)


def render_behavioral_drift(drift: pd.DataFrame) -> None:
    st.subheader("Evolution du taux de cooperation")
    if drift.empty:
        st.info("Aucune evolution comportementale disponible.")
        return

    fig = px.line(
        drift.sort_values("round_bucket"),
        x="round_bucket",
        y="cooperation_rate",
        color="strategy_name",
        line_dash="run_id" if drift["run_id"].nunique() > 1 else None,
        markers=True,
        labels={"round_bucket": "Bucket de tours", "cooperation_rate": "Taux de cooperation"},
    )
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)


def render_forgiveness(forgiveness: pd.DataFrame) -> None:
    st.subheader("Indice de pardon")
    if forgiveness.empty:
        st.info("Aucun indice de pardon disponible.")
        return

    fig = px.bar(
        forgiveness.sort_values("forgiveness_rate", ascending=False),
        x="strategy_name",
        y="forgiveness_rate",
        color="strategy_type",
        hover_data=["betrayal_events", "forgiveness_events"],
        labels={
            "strategy_name": "Strategie",
            "forgiveness_rate": "Taux de retour a la cooperation",
        },
    )
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)


def render_run_comparison(run_comparison: pd.DataFrame) -> None:
    st.subheader("Comparaison des runs")
    if run_comparison.empty:
        st.info("Aucune comparaison de runs disponible.")
        return

    fig = px.scatter(
        run_comparison,
        x="cooperation_rate",
        y="avg_score_per_round",
        size="total_score",
        color="strategy_name",
        hover_data=["run_id", "rank", "forgiveness_rate"],
        labels={
            "cooperation_rate": "Taux de cooperation",
            "avg_score_per_round": "Score moyen par tour",
        },
    )
    fig.update_xaxes(tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)


def render_tables(tables: dict[str, pd.DataFrame]) -> None:
    st.subheader("Tables Gold")
    for name, table in tables.items():
        with st.expander(name):
            st.dataframe(table, use_container_width=True)


if __name__ == "__main__":
    main()
