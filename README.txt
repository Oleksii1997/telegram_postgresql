About project:
This is a telegram bot that shows the weather with database postgresql.

Version 1.0:
A bot can get a city name in three ways:
- we get geolocation (the "geopy" library is used);
- we get city name (check the name of the city and the corresponding URL on the site sinoptic.ua)
- choseing city name (region -> district -> city name) from database (uses PostgreSQL, code to create and populate the database
    in "create_db.py" (WARNING: you can used dump in "dump_bd" folder), to obtain a list of regions, districts and cities
    used "selenium", site sinoptic.ua)

Weather information is obtained from the site sinoptic.ua using "beautifulsoup4"



