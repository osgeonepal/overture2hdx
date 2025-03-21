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

Example 
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
config_yaml_mini = f"""
    iso3: npl
    geom: {geom}
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
            title: Roads of Pokhara Nepal
            notes:  Overturemaps Export for Pokhara . Data might known to have errors however gone through validation checks to detect map errors, breakage, and vandalism . Sources would be combination of OSM and Other openly available datasets in the region including facebook roads and ESRI community datasets
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

    - Buildings:
        select:
            - id
            - names.primary as name
            - class as class
            - subtype as subtype
            - height as height
            - level as level
            - num_floors as num_floors
            - UNNEST(JSON_EXTRACT(sources, '$[*].dataset')) AS source
        hdx:
            title: Buildings of Pokhara Nepal
            notes:  Overturemaps Export for Nepal . Data might known to have errors however gone through validation checks to detect map errors, breakage, and vandalism . Sources would be combination of OSM and Other openly available datasets in the region including facebook roads and ESRI community datasets
            tags:
            - geodata
        theme:
            - buildings
        feature_type:
            - building
        formats:
            - gpkg
            - shp
    """


from overture2hdx import Config, Exporter

config = Config(config_yaml=config_yaml_mini)
exporter = Exporter(config)
results = exporter.export()
print(results)
```

### How it works?
<img src="https://github.com/user-attachments/assets/c15e09eb-b2d2-4d05-8212-414ab097dd65" alt="overture2hdx" height="800">

### Author and License 
Kshitij Raj Sharma , License : GNU GENERAL PUBLIC LICENSE V3
