# Szkielet raportu

## 1. Tytuł projektu i skład zespołu

Wpisz:

- tytuł projektu,
- skład sekcji,
- przedmiot,
- prowadzącego,
- datę oddania.

## 2. Opis analizowanego problemu

Opisz:

- dlaczego temat jest ważny,
- czym są zmiany klimatyczne w kontekście Europy,
- dlaczego ptaki są dobrym bioindykatorem,
- dlaczego wybrałyście te trzy gatunki.

## 3. Szczegółowy opis zbiorów danych

### 3.1 Europejski Monitoring Ptaków (PECBMS)

- co mierzy ten zbiór,
- zakres lat,
- definicja indeksu populacji,
- ograniczenia i zalety.

### 3.2 GBIF

- co oznaczają rekordy wystąpień,
- jakie pola pobieramy,
- jak filtrujemy dane,
- dlaczego nie traktujemy tego zbioru jako bezpośredniej miary liczebności populacji.

### 3.3 Dane klimatyczne

- z jakiego API pochodzą dane,
- jakie zmienne są pobierane,
- jak budowany jest zagregowany indeks klimatu dla Europy,
- jak wyznaczany jest okres bazowy do odchyleń temperatury.

## 4. Załadowanie danych i pre-processing

Pokaż:

- wczytanie arkuszy Excel przez `pandas.read_excel`,
- pobieranie JSON z API i normalizację do `DataFrame`,
- standaryzację nazw kolumn,
- konwersję typów,
- usuwanie braków i rekordów bez współrzędnych,
- ograniczenie analiz do miesięcy sezonu lęgowego,
- budowę pól siatki i wskaźników zasięgu.

## 5. Analiza wizualna

Pokaż:

- wykres indeksu populacji w czasie,
- wykres liczby zajmowanych pól siatki,
- wykres środka zasięgu obserwacji,
- wykres temperatury i odchylenia klimatycznego,
- zrzuty ekranu z dashboardu.

## 6. Analiza statystyczna

Uwzględnij:

- statystyki opisowe,
- analizę rozkładu,
- korelację Pearsona i Spearmana,
- test trendu liniowego,
- porównanie okresów,
- test stabilności szeregu czasowego ADF.

## 7. Analiza zaawansowana

Najbezpieczniejsza wersja do oddania:

- analiza szeregu czasowego indeksu populacji,
- analiza zmian zasięgu w czasie,
- prosty model predykcyjny lub projekcja trendu,
- porównanie gatunków w jednym panelu analitycznym.

## 8. Wyniki i wnioski

Odpowiedz wprost:

- który gatunek reaguje najsilniej,
- czy widać przesunięcie na północ,
- czy wzrost temperatury ma podobny związek dla wszystkich gatunków,
- jakie są ograniczenia interpretacyjne.

## 9. Załączniki

- kod źródłowy,
- notatnik Jupyter,
- prezentacja PowerPoint,
- opcjonalnie zrzuty ekranu z aplikacji.
