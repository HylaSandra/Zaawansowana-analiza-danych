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
- `docs/report_outline.md` - szkic raportu
- `docs/presentation_outline.md` - szkic prezentacji

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

## Wdrożenie na Render

Repozytorium jest przygotowane pod wdrożenie jako `Render Web Service`:

- `render.yaml` definiuje usługę Render,
- `.python-version` przypina serię Pythona do `3.11`,
- aplikacja korzysta z gotowych plików w `data/processed`, więc na Render nie trzeba uruchamiać pipeline'u pobierającego dane z `GBIF` i `Open-Meteo`.

Najprostsza ścieżka wdrożenia:

1. Wypchnij repozytorium na GitHub.
2. Upewnij się, że w repo są również pliki z `data/processed`.
3. Zaloguj się do Render.
4. Wybierz `New +` -> `Blueprint`.
5. Wskaż repozytorium z projektem.
6. Render wykryje `render.yaml` i utworzy usługę.
7. Po pierwszym deployu aplikacja będzie dostępna pod adresem `onrender.com`.

Uwaga: na darmowym planie pierwsze otwarcie aplikacji po dłuższej bezczynności może potrwać chwilę, bo usługa bywa usypiana.

Jeśli wolisz utworzyć usługę ręcznie zamiast przez Blueprint, użyj tych samych komend:

- Build Command:

```bash
pip install -r requirements.txt
```

- Start Command:

```bash
python -m streamlit run app/dashboard.py --server.headless=true --server.address=0.0.0.0 --server.port=$PORT
```

W Render warto też ustawić:

- `Environment`: `Python 3`
- region: `Frankfurt`
- zmienna środowiskowa `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false`

## Aktualizacja danych przed kolejnym deployem

Jeśli chcesz odświeżyć dane przed ponownym wdrożeniem:

1. Uruchom lokalnie:

```powershell
python scripts/build_dataset.py
```

2. Sprawdź zaktualizowane pliki w `data/processed`.
3. Dodaj je do commita razem ze zmianami w kodzie.
4. Wypchnij zmiany na GitHub.
5. Render wykona redeploy z nowymi wynikami.

## Co pokazać w dashboardzie

- wybór gatunku,
- wykres indeksu populacji w czasie,
- wykres liczby zajmowanych pól siatki,
- wykres przesunięcia środka zasięgu obserwacji,
- wykres temperatury i odchylenia klimatycznego,
- wykres zależności między temperaturą a indeksem populacji,
- tabela z wynikami testów statystycznych,
- widok `Podsumowanie i wnioski`.

## Jak to wpisać do raportu

Temat pracy jest dobrze zgodny z wymaganiami prowadzącego:

- załadowanie danych do `DataFrame`,
- pre-processing,
- analiza wizualna,
- analiza statystyczna,
- analiza zaawansowana,
- podsumowanie i wnioski.

## Ograniczenia

- dane `GBIF` są wrażliwe na wysiłek obserwacyjny,
- indeks klimatu dla Europy jest tu budowany jako agregat dla reprezentatywnych punktów,
- projekt pokazuje związek statystyczny, a nie twardą zależność przyczynową.
