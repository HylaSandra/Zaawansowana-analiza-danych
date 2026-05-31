# Dane referencyjne zasięgu

Plik `known_range_cells.csv` przechowuje komórki znanego zasięgu gatunków używane w widoku `Obserwacje vs zasięg`.

Oczekiwany format:

```csv
scientific_name,cell_id,center_latitude,center_longitude,source
Ciconia ciconia,example-cell,52.0,21.0,EBBA2 50-km occurrence
```

Rekomendowane źródło: EBBA2 50-km occurrence data. Według EBBA2 dane occurrence 50 km dla wszystkich gatunków i całego obszaru badania są open access w formacie CSV. Komórki powinny reprezentować zajęte kwadraty atlasowe, a `center_latitude` i `center_longitude` środek komórki w układzie WGS84.
