import json

geom = json.dumps(
    {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "coordinates": [
                        [
                            [83.98047393581618, 28.255338988044088],
                            [83.973540694181, 28.230486421513703],
                            [83.91927014759125, 28.214265947308945],
                            [83.97832224013575, 28.195093119231174],
                            [83.96971545741735, 28.158212628626416],
                            [84.00175181531534, 28.19361814379657],
                            [84.03187555483152, 28.168540447741847],
                            [84.01059767533235, 28.208788347541898],
                            [84.0342663278089, 28.255549578267903],
                            [83.99960011963498, 28.228801292171724],
                            [83.98047393581618, 28.255338988044088],
                        ]
                    ],
                    "type": "Polygon",
                },
            }
        ],
    }
)
iso3 = "NPL"
dataset_name = "Pokhara, Nepal"
key = "osegonepal_pkr"
subnational = True
frequency = "yearly"

config_yaml = f"""
iso3: {iso3}
geom: {geom}
key: {key}
subnational: {subnational}
frequency: {frequency}
categories:

- Hospitals:
    select:
        - id
        - names.primary as name
        - names.common.en as name_en
        - categories.primary as category
    hdx:
        title: Hospitals of {dataset_name}
        notes: This dataset includes health POIs (e.g., hospitals and clinics) from the Overture Places theme, derived from open data provided by Meta and Microsoft. Useful for public health logistics and emergency response. Read More, https://docs.overturemaps.org/guides/places/
        tags:
        - health
        license: CDLA Permissive 2.0
        caveats: Contains hospital locations from the Overture Places theme, derived from Meta and Microsoft data. Licensed under CDLA Permissive 2.0. Data might contain errors and was scraped and published using the Overture public release via the overture2hdx package.

- Schools:
    select:
        - id
        - names.primary as name
        - names.common.en as name_en
        - categories.primary as category
    hdx:
        title: Schools of {dataset_name}
        notes: This dataset captures education POIs (e.g., schools and universities) from the Overture Places theme, using Meta and Microsoft open data. Read More, https://docs.overturemaps.org/guides/places/
        tags:
        - education
        license: CDLA Permissive 2.0
        caveats: Contains school POIs from Meta and Microsoft via Overture Places. Licensed under CDLA Permissive 2.0. Data might contain errors and was scraped and published using the Overture public release via the overture2hdx package.

- Rivers:
    select:
        - id
        - names.primary as name
        - names.common.en as name_en
        - subtype
        - class
    hdx:
        title: Rivers of {dataset_name}
        notes: This dataset contains rivers, lakes, and other water features from the Overture Base theme, primarily sourced from OpenStreetMap. Read More, https://docs.overturemaps.org/guides/base/
        tags:
        - environment
        license: ODbL 1.0
        caveats: Includes OpenStreetMap-derived hydrography under the Open Database License (ODbL). Share-alike and attribution are required. Data might contain errors and was scraped and published using the Overture public release via the overture2hdx package.

- Land Use:
    select:
        - id
        - names.primary as name
        - names.common.en as name_en
        - subtype
        - class
    hdx:
        title: Land Use of {dataset_name}
        notes: This dataset covers land use polygons (e.g., farmland, forests) from the Overture Base theme, derived primarily from OpenStreetMap landuse tags. Read More, https://docs.overturemaps.org/guides/base/
        tags:
        - environment
        license: ODbL 1.0
        caveats: Contains land use data derived from OpenStreetMap. Distributed under ODbL v1.0. Attribution and share-alike are required. Data might contain errors and was scraped and published using the Overture public release via the overture2hdx package.

- Transportation Hubs:
    select:
        - id
        - names.primary as name
        - names.common.en as name_en
        - categories.primary as category
    hdx:
        title: Transportation Hubs of {dataset_name}
        notes: This dataset includes airports, train stations, and terminals from the Overture Places theme, derived from Meta and Microsoft open data. Read More, https://docs.overturemaps.org/guides/places/
        tags:
        - transportation
        - logistics
        license: CDLA Permissive 2.0
        caveats: Contains transportation POIs (e.g., airports, stations) from Meta and Microsoft via Overture Places. Licensed under CDLA Permissive 2.0. Data might contain errors and was scraped and published using the Overture public release via the overture2hdx package.

- Settlements:
    select:
        - id
        - names.primary as name
        - names.common.en as name_en
        - population
        - country
    hdx:
        title: Settlements of {dataset_name}
        notes: This dataset includes populated places (cities, towns, villages, hamlets) from the Overture Divisions theme, which merges boundaries from OpenStreetMap, geoBoundaries, and Esri. Read More, https://docs.overturemaps.org/guides/divisions/
        tags:
        - population
        license: ODbL 1.0
        caveats: Includes settlement-level boundaries from OSM (ODbL), geoBoundaries (CC BY), and Esri (CC BY). Final dataset is ODbL-licensed. Share-alike and attribution required. Data might contain errors and was scraped and published using the Overture public release via the overture2hdx package.

- Roads:
    select:
        - id
        - names.primary as name
        - names.common.en as name_en
        - class as class
        - subclass as subclass
        - UNNEST(JSON_EXTRACT(road_surface, '$[*].value')) as road_surface
        - UNNEST(JSON_EXTRACT(sources, '$[*].dataset')) AS source
    hdx:
        title: Roads of {dataset_name}
        notes: This dataset includes road networks (e.g., highways, local roads) from the Overture Transportation theme, sourced from OpenStreetMap and TomTom. Read More, https://docs.overturemaps.org/guides/transportation/
        tags:
        - geodata
        - transportation
        - roads
        license: ODbL 1.0
        caveats: Contains roads from OSM and TomTom via Overture. Licensed under ODbL v1.0. Attribution and share-alike required. Data might contain errors and was scraped and published using the Overture public release via the overture2hdx package.

- Buildings:
    select:
        - id
        - names.primary as name
        - names.common.en as name_en
        - class as class
        - subtype as subtype
        - height as height
        - level as level
        - num_floors as num_floors
        - UNNEST(JSON_EXTRACT(sources, '$[*].dataset')) AS source
    hdx:
        title: Buildings of {dataset_name}
        notes: This dataset includes building footprints from the Overture Buildings theme. Sources include OSM, Microsoft Global ML Buildings, Google Open Buildings, and Esri Community Maps. Read More, https://docs.overturemaps.org/guides/buildings/
        tags:
        - geodata
        - buildings
        - infrastructure
        license: ODbL 1.0
        caveats: Includes building data from OSM (ODbL), Microsoft (ODbL), Google (CC BY), and Esri (CC BY). Final dataset is ODbL-licensed. Attribution and share-alike required. Data might contain errors and was scraped and published using the Overture public release via the overture2hdx package.
"""


from overture2hdx import Config, Exporter

config = Config(config_yaml=config_yaml)
exporter = Exporter(config)
results = exporter.export()
print(results)
