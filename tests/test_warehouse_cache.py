"""Test della cache su disco."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from openzone.warehouse import Cache
from openzone.warehouse.cache import CacheEntry, CacheStats


@pytest.fixture
def frame() -> pd.DataFrame:
    """DataFrame di esempio da mettere in cache."""
    return pd.DataFrame({"event_id": ["e1", "e2"], "x": [10.0, 20.0]})


@pytest.fixture
def cache(tmp_path: Path) -> Cache:
    """Cache vuota in una directory temporanea."""
    return Cache(root=tmp_path, namespace="prova")


def test_key_is_deterministic() -> None:
    """Gli stessi parametri producono la stessa chiave, in ordine diverso."""
    first = Cache.key("shots", league="Serie A", season="2024")
    second = Cache.key("shots", season="2024", league="Serie A")
    assert first == second
    assert len(first) == 64


def test_key_changes_with_parameters() -> None:
    """Parametri diversi producono chiavi diverse."""
    assert Cache.key("shots", season="2024") != Cache.key("shots", season="2025")
    assert Cache.key("shots") != Cache.key("passes")


def test_put_and_get_roundtrip(cache: Cache, frame: pd.DataFrame) -> None:
    """Ciò che si scrive si rilegge identico, con la provenienza allegata."""
    key = cache.key("eventi", match_id=1)
    assert cache.put(key, frame, match_id=1).rows == 2
    restored = cache.get(key)
    assert restored is not None
    pd.testing.assert_frame_equal(restored, frame)
    assert restored.attrs["openzone.cache_key"] == key
    assert restored.attrs["openzone.cache_namespace"] == "prova"


def test_get_missing_returns_none(cache: Cache) -> None:
    """Una chiave assente restituisce ``None``, non un errore."""
    assert cache.get(cache.key("assente")) is None
    assert cache.has(cache.key("assente")) is False


def test_put_requires_a_dataframe(cache: Cache) -> None:
    """La cache salva solo DataFrame: altro input è un errore."""
    with pytest.raises(TypeError):
        cache.put(cache.key("x"), {"a": 1})  # type: ignore[arg-type]


def test_invalid_key_is_rejected(cache: Cache) -> None:
    """Una chiave malformata è un errore, non una scrittura in un percorso arbitrario."""
    with pytest.raises(ValueError):
        cache.get("non-una-chiave")


def test_entries_and_stats(cache: Cache, frame: pd.DataFrame) -> None:
    """Le voci e le statistiche riflettono il contenuto del namespace."""
    for index in range(3):
        cache.put(cache.key("eventi", match_id=index), frame, match_id=index)
    entries = cache.entries()
    assert len(entries) == 3
    assert all(isinstance(entry, CacheEntry) for entry in entries)
    stats = cache.stats()
    assert isinstance(stats, CacheStats)
    assert stats.entries == 3
    assert stats.bytes_on_disk > 0
    assert stats.newest is not None and stats.oldest is not None
    assert stats.newest >= stats.oldest


def test_stats_on_empty_namespace(cache: Cache) -> None:
    """Un namespace vuoto riporta zeri, senza valori inventati."""
    stats = cache.stats()
    assert stats.entries == 0
    assert stats.bytes_on_disk == 0
    assert stats.oldest is None


def test_delete_removes_the_entry(cache: Cache, frame: pd.DataFrame) -> None:
    """La cancellazione rimuove dati e metadati."""
    key = cache.key("eventi")
    cache.put(key, frame)
    assert cache.delete(key) is True
    assert cache.has(key) is False
    assert cache.delete(key) is False


def test_evict_removes_old_entries(cache: Cache, frame: pd.DataFrame) -> None:
    """L'eviction per età rimuove le voci più vecchie della soglia."""
    cache.put(cache.key("vecchia"), frame)
    assert cache.evict(older_than_seconds=3600) == 0
    assert cache.evict(older_than_seconds=0) == 1
    assert cache.entries() == []


def test_evict_rejects_negative_age(cache: Cache) -> None:
    """Una soglia negativa è un errore."""
    with pytest.raises(ValueError):
        cache.evict(older_than_seconds=-1)


def test_clear_empties_the_namespace(cache: Cache, frame: pd.DataFrame) -> None:
    """``clear`` svuota il namespace e lo lascia pronto all'uso."""
    cache.put(cache.key("eventi"), frame)
    cache.clear()
    assert cache.entries() == []
    assert cache.directory.is_dir()


def test_namespaces_are_isolated(tmp_path: Path, frame: pd.DataFrame) -> None:
    """Due namespace non si vedono: dati grezzi e dati derivati non si sovrascrivono."""
    raw = Cache(root=tmp_path, namespace="grezzi")
    derived = Cache(root=tmp_path, namespace="derivati")
    key = Cache.key("eventi")
    raw.put(key, frame)
    assert raw.has(key) is True
    assert derived.has(key) is False


def test_default_root_uses_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """La directory radice è sovrascrivibile dall'ambiente."""
    from openzone.warehouse.cache import default_root

    monkeypatch.setenv("OPENZONE_CACHE_DIR", str(tmp_path / "cache"))
    assert default_root() == (tmp_path / "cache").resolve()


def test_repr_is_informative(cache: Cache) -> None:
    """La rappresentazione mostra namespace e directory."""
    text = repr(cache)
    assert "Cache(" in text
    assert "prova" in text
