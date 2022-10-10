# Spletni pajek

Spletni pajek je bil sprogramiran na Linux Ubuntu 18.04 sistemih, na katerih je bilo tudi testirano njegovo delovanje.

Za zagon pajka je potrebno izvseti naslednje korake:
+ lokacija chromedriverja: /usr/bin/chromedriver (za Unix)
+ ustvarjanje okolja: conda create -n wier python=3.6
+ aktivacija okolja: conda activate wier
+ conda install nb_conda
+ instalacija knjiznice BeautifulSoup: pip install beautifulsoup4
+ pip install json
+ za parsanje sitemapov: pip install ultimate_sitemap_parser
+ ustvarjanje baze z dockerjem: docker run --name postgresql-wier -e POSTGRES_PASSWORD=SecretPassword -e POSTGRES_USER=user -v $PWD/pgdata:/var/lib/postgresql/data -v $PWD/init-scripts:/docker-entrypoint-initdb.d -p 5432:5432 -d postgres:9

Pajka poženemo z ukazom python fetch-data-frontier.py. Vsa programska koda za njegovo izvajanje se nahaja v tej datoteki in datoteki dbfunctions.py, ki vsebuje vse funkcije za manipulacijo baze. Ostale datoteke v mapi so bile uporabljene zgolj za testiranje in vmesne faze razvoja in niso del koncne verzije pajka.
