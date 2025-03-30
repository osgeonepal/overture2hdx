# Overture Map Data 2 HDX

This project is designed to export geographic data from Overture Maps and upload it to the Humanitarian Data Exchange (HDX). The data is processed using DuckDB and can be exported in various formats such as GeoJSON, GPKG, and ESRI Shapefile.

## Features

- Export geographic data from Overture Maps.
- Upload data to HDX.
- Support for multiple output formats.
- Configurable via YAML and environment variables.
- Logging setup using environment variables or parameters.


## Installation

```bash
pip install overture2hdx
```

## Configuration

The application is configured using a YAML file and environment variables.

### YAML Configuration

Example `config.yaml`:
```yaml
iso3: npl
geom: '{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": {"coordinates": [[]], "type": "Polygon"}}]}'
key: osgeonepal_pkr
subnational: true
frequency: yearly
categories:
- Roads:
    select:
        - id
        - names.primary as name
        - class as class
        - subclass as subclass
        - UNNEST(JSON_EXTRACT(road_surface, '$[*].value')) as road_surface
        - UNNEST(JSON_EXTRACT(sources, '$[*].dataset')) AS source
    hdx:
        title: Roads of Pokhara
        notes: Overturemaps Export for Pokhara. Data might have errors but has gone through validation checks.
        tags:
        - geodata
        - transportation
        - roads
    theme:
        - transportation
    feature_type:
        - segment
    formats:
        - gpkg
        - shp

```
### Code Overview

`Config`: Class to handle configuration.
`OvertureMapExporter`: Class to handle the export process.
`setup_logging`: Function to set up logging.


### Default export config 

Following is the default yaml used 
| Category               | Description                                                                                      | License              | Overture Theme Docs                                               | Attributes                                                                                                                                              | File Formats         |
|------------------------|--------------------------------------------------------------------------------------------------|-----------------------|-------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------|
| **Hospitals**          | Health POIs such as hospitals and clinics, sourced from Meta and Microsoft open data            | CDLA Permissive 2.0   | [Places](https://docs.overturemaps.org/guides/places/)           | `id`, `name`, `name_en`, `category`, `address`, `phone`, `email`, `website`, `confidence`, `source`                                                    | `gpkg`, `shp`        |
| **Schools**            | Educational POIs including schools, colleges, and universities from Meta and Microsoft          | CDLA Permissive 2.0   | [Places](https://docs.overturemaps.org/guides/places/)           | `id`, `name`, `name_en`, `category`, `address`, `phone`, `website`, `confidence`, `source`                                                              | `gpkg`, `shp`        |
| **Rivers**             | Rivers, lakes, and other water features from OpenStreetMap via the Base theme                   | ODbL 1.0              | [Base](https://docs.overturemaps.org/guides/base/)               | `id`, `name`, `name_en`, `subtype`, `class`, `is_salt`, `wikidata`, `source`                                                                            | `gpkg`, `shp`        |
| **Land Use**           | Land use areas like farmland and forests from OpenStreetMap landuse tags                        | ODbL 1.0              | [Base](https://docs.overturemaps.org/guides/base/)               | `id`, `name`, `name_en`, `subtype`, `class`, `surface`, `wikidata`, `source`                                                                            | `gpkg`, `shp`        |
| **Transportation Hubs**| POIs like airports, train stations, and terminals from Meta and Microsoft open data             | CDLA Permissive 2.0   | [Places](https://docs.overturemaps.org/guides/places/)           | `id`, `name`, `name_en`, `category`, `address`, `phone`, `website`, `confidence`, `source`                                                              | `gpkg`, `shp`        |
| **Settlements**        | Cities, towns, villages, and hamlets from OSM, geoBoundaries, and Esri                          | ODbL 1.0              | [Divisions](https://docs.overturemaps.org/guides/divisions/)     | `id`, `name`, `name_en`, `population`, `region`, `wikidata`, `source`                                                                                   | `gpkg`, `shp`        |
| **Roads**              | Roads including highways and local roads from OpenStreetMap and TomTom                          | ODbL 1.0              | [Transportation](https://docs.overturemaps.org/guides/transportation/) | `id`, `name`, `name_en`, `class`, `subclass`, `subtype`, `road_surface`, `source`                                                                      | `gpkg`, `shp`        |
| **Buildings**          | Building footprints from OSM, Microsoft, Google, and Esri                                       | ODbL 1.0              | [Buildings](https://docs.overturemaps.org/guides/buildings/)     | `id`, `name`, `name_en`, `class`, `subtype`, `height`, `level`, `num_floors`, `num_floors_underground`, `is_underground`, `has_parts`, `roof_material`, `roof_shape`, `roof_color`, `source` | `gpkg`, `shp`        |


### Default python example 

```python
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

from overture2hdx import DEFAULT_CONFIG_YAML

config_yaml = DEFAULT_CONFIG_YAML.format(
    iso3=iso3,
    geom=geom,
    key=key,
    subnational=subnational,
    frequency=frequency,
    dataset_name=dataset_name,
)


from overture2hdx import Config, Exporter

config = Config(config_yaml=config_yaml)
exporter = Exporter(config)
results = exporter.export()
print(results)
```

### How it works?
<img src="https://github.com/user-attachments/assets/c15e09eb-b2d2-4d05-8212-414ab097dd65" alt="overture2hdx" height="800">

### Author and License 
Kshitij Raj Sharma , License : GNU GENERAL PUBLIC LICENSE V3
