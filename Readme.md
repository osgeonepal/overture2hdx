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
iso3 = "NPL"
dataset_name = "Pokhara, Nepal"
key = "osegonepal_pkr_"
subnational = True
frequency = "yearly"
config_yaml = f"""
iso3: {iso3}
geom: {test_geom}
key: {key}
subnational: {subnational}
frequency: {frequency}
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
        title: Roads of {dataset_name}
        notes: Overturemaps export containing road data (e.g., highways, local roads). Data may contain known errors but has undergone validation to detect map issues. Sources include OSM, Facebook roads, ESRI, and other open datasets. Useful for transportation analysis and route planning. Read More, https://docs.overturemaps.org/
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
        title: Buildings of {dataset_name}
        notes: Overturemaps export containing building footprints. Data may contain known errors but has undergone validation. Includes OSM, ESRI, and Facebook-derived building data. Useful for building density studies and urban planning. Read More, https://docs.overturemaps.org/
        tags:
        - geodata
    theme:
        - buildings
    feature_type:
        - building
    formats:
        - gpkg
        - shp

- Healthcare Facilities:
    select:
        - id
        - names.primary as name
        - categories.primary as category
    hdx:
        title: Healthcare Facilities of {dataset_name}
        notes: This dataset includes health POIs (e.g., hospitals and clinics) from Overture Places. Useful for public health logistics and emergency response. Read More, https://docs.overturemaps.org/
        tags:
        - health
    theme:
        - places
    feature_type:
        - place
    where:
        - "categories.primary IN ('hospital', 'clinic')"
    formats:
        - gpkg
        - shp

- Educational Facilities:
    select:
        - id
        - names.primary as name
        - categories.primary as category
    hdx:
        title: Educational Facilities of {dataset_name}
        notes: This dataset captures education POIs (e.g., schools and universities) from Overture Places. Helpful for response planning, shelter identification, and educational facility analysis. Read More, https://docs.overturemaps.org/
        tags:
        - education
    theme:
        - places
    feature_type:
        - place
    where:
        - "categories.primary IN ('school', 'university', 'college')"
    formats:
        - gpkg
        - shp

- Water Bodies:
    select:
        - id
        - names.primary as name
        - subtype
        - class
    hdx:
        title: Water Bodies of {dataset_name}
        notes: This dataset contains rivers, lakes, and other water bodies from Overture Base data. Important for environmental monitoring and disaster analysis. Read More, https://docs.overturemaps.org/
        tags:
        - environment
    theme:
        - base
    feature_type:
        - water
    where:
        - "class NOT IN ('dam', 'weir', 'breakwater', 'fountain', 'drinking_water')"
    formats:
        - gpkg
        - shp

- Land Use:
    select:
        - id
        - names.primary as name
        - subtype
        - class
    hdx:
        title: Land Use of {dataset_name}
        notes: This dataset covers various land use areas (e.g., farmland, forests) from Overture Base data. Useful for planning, resource management, and disaster recovery efforts. Read More, https://docs.overturemaps.org/
        tags:
        - environment
    theme:
        - base
    feature_type:
        - land_use
    formats:
        - gpkg
        - shp

- Transportation Hubs:
    select:
        - id
        - names.primary as name
        - categories.primary as category
    hdx:
        title: Transportation Hubs of {dataset_name}
        notes: This dataset includes airports, stations, and terminals from Overture Places. A key resource for mapping mobility infrastructure and logistics. Read More, https://docs.overturemaps.org/
        tags:
        - transportation
        - logistics
    theme:
        - places
    feature_type:
        - place
    where:
        - "categories.primary IN ('airport', 'train_station', 'bus_station', 'light_rail_and_subway_stations', 'ferry_terminal')"
    formats:
        - gpkg
        - shp

- Settlements:
    select:
        - id
        - names.primary as name
        - population
        - country
    hdx:
        title: Settlements of {dataset_name}
        notes: This dataset references populated places (cities, towns, villages, hamlets) from Overture Divisions. Crucial for situational awareness and planning. Read More, https://docs.overturemaps.org/
        tags:
        - population
    theme:
        - divisions
    feature_type:
        - division
    where:
        - "subtype = 'locality'"
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
