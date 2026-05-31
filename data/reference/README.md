# Dane referencyjne zasięgu

Plik `known_range_cells.csv` przechowuje komórki znanego zasięgu gatunków używane w widoku `Obserwacje vs zasięg`.

Oczekiwany format:

```csv
scientific_name,cell_id,center_latitude,center_longitude,south_latitude,north_latitude,west_longitude,east_longitude,source
Ciconia ciconia,example-cell,52.0,21.0,51.75,52.25,20.625,21.375,EBBA2 50-km occurrence
```

Obecny plik zawiera przybliżoną siatkę referencyjną 50-km-ish przygotowaną po to, żeby widok `Obserwacje vs zasięg` działał w dashboardzie bez dodatkowego logowania do zewnętrznego serwisu. Źródło w kolumnie `source` jest opisane jako przybliżenie, a nie oryginalny eksport atlasowy.

Porównanie punktów z zasięgiem działa teraz po granicach komórek: punkt GBIF jest uznany za zgodny z zasięgiem tylko wtedy, gdy jego współrzędne mieszczą się między `south_latitude`, `north_latitude`, `west_longitude` i `east_longitude`.

Rekomendowane źródło docelowe: EBBA2 50-km occurrence data. Według EBBA2 dane occurrence 50 km dla wszystkich gatunków i całego obszaru badania są open access w formacie CSV. Po pobraniu oryginalnych danych można zastąpić nimi ten plik, zachowując kolumny `scientific_name`, `cell_id`, `center_latitude`, `center_longitude`, granice komórek i `source`.
