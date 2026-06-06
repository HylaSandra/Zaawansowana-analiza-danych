# Oficjalne dane referencyjne EBBA

Widok `Obserwacje vs zasięg` korzysta z rzeczywistych danych atlasowych:

- `ebba_grid_50km.geojson` zawiera oficjalne poligony komórek siatki EBBA 50 km;
- `ebba_occurrence_50km.csv` wskazuje komórki, w których dany gatunek został zgłoszony jako możliwy, prawdopodobny lub potwierdzony gatunek lęgowy w EBBA1 lub EBBA2.

Dane są budowane poleceniem:

```powershell
python scripts/build_ebba_reference.py
```

Skrypt pobiera:

- oficjalną warstwę występowania z finalnego serwisu map EBBA2: `https://ebba2.info/maps/`;
- geometrię siatki 50 km z serwisu mapowego EBBA: `https://mapviewer.ebba2.info/`.

## Przypisywanie okresu atlasowego

EBBA nie dostarcza rocznej mapy zasięgu. Projekt wykorzystuje dwa dostępne okresy:

- `EBBA1 (lata 80.)`, identyfikowany w danych rokiem 1985;
- `EBBA2 (2013-2017)`, identyfikowany w danych rokiem 2015.

Jeżeli rok punktu GBIF znajduje się wewnątrz okresu atlasowego, używany jest ten atlas. Dla pozostałych lat wybierany jest okres, którego najbliższa granica czasowa jest najbliższa rokowi obserwacji. Przy jednakowej odległości wybierany jest nowszy atlas.

Punkt jest uznawany za zgodny z zasięgiem wyłącznie wtedy, gdy znajduje się wewnątrz rzeczywistego poligonu komórki występowania odpowiedniego atlasu.
