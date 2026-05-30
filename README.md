# Jak zmiany klimatyczne wpływają na zasięg i populację wybranych gatunków ptaków?

Projekt został przygotowany jako interaktywny dashboard w Pythonie z wykorzystaniem `pandas`, `streamlit` i `plotly`. Analiza łączy trzy niezależne źródła danych:

1. `PECBMS`, czyli Europejski Monitoring Ptaków, do analizy zmian populacji w Europie.
2. `GBIF`, czyli globalną bazę obserwacji organizmów, do analizy zmian zasięgu obserwacji.
3. `Open-Meteo` jako publiczny interfejs do historycznych danych klimatycznych.

## Proponowane gatunki

- `Ciconia ciconia` - bocian biały
- `Hirundo rustica` - jaskółka dymówka
- `Cuculus canorus` - kukułka

## Pytania badawcze

1. Czy wzrost temperatury w Europie jest powiązany ze zmianami indeksu populacji wybranych gatunków?
2. Czy w danych obserwacyjnych widać przesunięcie zasięgu na północ lub zmianę liczby zajmowanych pól siatki?
3. Czy zależności są podobne dla gatunków o różnej ekologii i różnych trendach populacyjnych?

## Hipotezy

1. Gatunki migracyjne i związane z krajobrazem rolniczym będą silniej reagować spadkiem indeksu populacji.
2. W danych wystąpień widoczne będą przesunięcia środka zasięgu obserwacji ku wyższym szerokościom geograficznym.
3. Korelacja między temperaturą sezonu lęgowego a wskaźnikami ptaków będzie różniła się między gatunkami.

## Dane i źródła

- PECBMS
  - opis: [PECBMS - Trends of wild birds in Europe, 2025 update](https://pecbms.info/trends-of-wild-birds-in-europe-2025-update/)
- GBIF
  - dokumentacja: [GBIF Occurrence API](https://techdocs.gbif.org/en/openapi/v1/occurrence)
- Open-Meteo
  - dokumentacja: [Historical Weather / Historical Forecast docs](https://open-meteo.com/en/docs/historical-forecast-api)

## Dobra praktyka metodologiczna

`GBIF` nie jest bezpośrednim pomiarem liczebności populacji. W tym projekcie traktujemy te dane jako przybliżenie zmian zasięgu obserwacji, a nie bezwzględną liczebność. Dlatego:

- populacje analizujemy głównie na podstawie `PECBMS`,
- zasięg analizujemy na podstawie pól siatki i środka zasięgu obserwacji z `GBIF`,
- wyniki interpretujemy ostrożnie i opisujemy ograniczenia danych obserwacyjnych.

## Struktura projektu

- `app/dashboard.py` - dashboard w Streamlit
- `scripts/build_dataset.py` - pipeline pobierania i przygotowania danych
- `src/climate_birds/config.py` - konfiguracja projektu
- `src/climate_birds/data_sources/pecbms.py` - dane populacyjne
- `src/climate_birds/data_sources/gbif.py` - dane o wystąpieniach
- `src/climate_birds/data_sources/climate.py` - indeks klimatu
- `src/climate_birds/processing.py` - agregacja i łączenie danych
- `src/climate_birds/statistics.py` - statystyki i testy

## Jak uruchomić projekt lokalnie

1. Zainstaluj Pythona 3.11 lub nowszego.
2. Utwórz środowisko wirtualne.
3. Zainstaluj zależności:

```powershell
pip install -r requirements.txt
```

4. Zbuduj lokalne zbiory danych:

```powershell
python scripts/build_dataset.py
```

5. Uruchom dashboard:

```powershell
python -m streamlit run app/dashboard.py
```

## Ograniczenia

- dane `GBIF` są wrażliwe na wysiłek obserwacyjny,
- indeks klimatu dla Europy jest tu budowany jako agregat dla reprezentatywnych punktów,
- projekt pokazuje związek statystyczny, a nie twardą zależność przyczynową.
