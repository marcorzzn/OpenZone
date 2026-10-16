"""Clustering delle azioni.

Raggruppare azioni simili (per geometria, esito, contesto) serve a passare da metriche
per evento a tipologie di giocata: per esempio distinguere le costruzioni dal basso dai
lanci lunghi, o i cross dalle combinazioni strette.

Due trappole da evitare, e il motivo per cui questo modulo è esplicito sui parametri:

* **clustering su feature non standardizzate**: le coordinate in metri dominano sulle
  variabili binarie, e il risultato diventa "dove" invece di "come";
* **etichette inventate a posteriori**: i cluster vanno interpretati guardando i loro
  centroidi e le loro dimensioni, e l'interpretazione va scritta, non improvvisata.

Il modulo richiede ``scikit-learn`` (extra ``models``).

Example:
    >>> from openzone.models import clustering
    >>> clustering.available()
    False
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from openzone._deps import has

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd

__all__ = ["ALGORITHMS", "available", "cluster_actions", "describe_clusters"]

#: Algoritmi ammessi e loro adeguatezza.
ALGORITHMS: dict[str, str] = {
    "kmeans": "Veloce, richiede di scegliere il numero di cluster e assume cluster sferici.",
    "hdbscan": "Trova il numero di cluster, gestisce forme irregolari e rumore.",
    "agglomerative": "Gerarchico: utile per esplorare la struttura prima di fissare k.",
}


def available() -> bool:
    """Indica se le dipendenze del clustering sono installate.

    Returns:
        ``True`` se ``scikit-learn`` è importabile.
    """
    return has("sklearn")


def cluster_actions(
    actions: pd.DataFrame,
    features: list[str],
    *,
    algorithm: Literal["kmeans", "hdbscan", "agglomerative"] = "kmeans",
    n_clusters: int | None = None,
    standardise: bool = True,
    **kwargs: Any,
) -> pd.DataFrame:
    """Raggruppa le azioni in cluster.

    Args:
        actions: Tabella di azioni con le feature da usare.
        features: Colonne da usare come feature.
        algorithm: Algoritmo, fra quelli in :data:`ALGORITHMS`.
        n_clusters: Numero di cluster, richiesto da ``kmeans`` e ``agglomerative``.
        standardise: Standardizza le feature prima del calcolo. Va lasciato attivo
            quasi sempre: senza, l'unità di misura decide il risultato.
        **kwargs: Iperparametri aggiuntivi dell'algoritmo.

    Returns:
        Le azioni con le colonne ``cluster`` e ``distance_to_centroid``.

    Raises:
        MissingDependencyError: Se ``scikit-learn`` non è installato.
        NotImplementedError: Previsto in Fase 3.
    """
    if not available():
        from openzone._deps import require

        require("sklearn")
    _ = (actions, features, algorithm, n_clusters, standardise, kwargs)
    raise NotImplementedError("models.clustering.cluster_actions: previsto in Fase 3.")


def describe_clusters(actions: pd.DataFrame, by: str = "cluster") -> pd.DataFrame:
    """Riassume i cluster per interpretarli invece di indovinarli.

    Args:
        actions: Azioni con la colonna dei cluster.
        by: Nome della colonna dei cluster.

    Returns:
        DataFrame con dimensione, centroidi e feature più caratterizzanti per cluster.

    Raises:
        NotImplementedError: Previsto in Fase 3, insieme a :func:`cluster_actions`.
    """
    _ = (actions, by)
    raise NotImplementedError("models.clustering.describe_clusters: previsto in Fase 3.")
