# RTA
Repozytorium na projekt RTA

Opis najważniejszych plików wykorzystywanych w projekcie:

alerts.py - plik odpowiadający za wyświetlanie powiadomień o zaistniałych arbitrażach w konsoli oraz dashboardzie \
arbitrage.py - plik obliczający arbitraż oraz podział środków pomiędzy bukmacherów \
docker-compose.yml - plik odpowiadający za działanie kafki wewnątrz konetera \ 
file_mock_api.py - plika zawierający funkcję imitującą API na podstawie danych wygenerowanych przy pliku generator.py \
generator.py - plik generujący lokalny strumień danych, zastępujący oryginalne API bukmacherskie na potrzeby prezentacji \
producer.py - plik pobierający dane z API (albo sztucznego mock_api) i przesyłający je dalej do kafki \
requirements.txt - wykorzystywane pakiety w projekcie dla Pythona 3.11.\* \
run_pipelineM.py - plik który załącza wszystkie procesy w odpowiedniej kolejności \
