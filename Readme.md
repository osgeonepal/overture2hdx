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

| Category              | Description                                                                                   | License              | Overture Theme Docs                                              | Attributes                                                                                          | File Formats         |
|-----------------------|-----------------------------------------------------------------------------------------------|----------------------|------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|----------------------|
| **Hospitals**         | Health POIs like hospitals and clinics, from Meta and Microsoft open data                     | CDLA Permissive 2.0  | [Places](https://docs.overturemaps.org/guides/places/)          | `id`, `names.primary`, `names.common.en`, `categories.primary`                                      | `gpkg`, `shp`        |
| **Schools**           | Education POIs like schools, colleges, universities from Meta and Microsoft                   | CDLA Permissive 2.0  | [Places](https://docs.overturemaps.org/guides/places/)          | `id`, `names.primary`, `names.common.en`, `categories.primary`                                      | `gpkg`, `shp`        |
| **Rivers**            | Water bodies (rivers, lakes, etc.) from OpenStreetMap via the Base theme                      | ODbL 1.0             | [Base](https://docs.overturemaps.org/guides/base/)              | `id`, `names.primary`, `names.common.en`, `subtype`, `class`                                        | `gpkg`, `shp`        |
| **Land Use**          | Land use polygons (farmland, forest, etc.) based on OSM landuse tags                          | ODbL 1.0             | [Base](https://docs.overturemaps.org/guides/base/)              | `id`, `names.primary`, `names.common.en`, `subtype`, `class`                                        | `gpkg`, `shp`        |
| **Transportation Hubs** | Airports, stations, terminals from Meta & Microsoft                                          | CDLA Permissive 2.0  | [Places](https://docs.overturemaps.org/guides/places/)          | `id`, `names.primary`, `names.common.en`, `categories.primary`                                      | `gpkg`, `shp`        |
| **Settlements**       | Populated places like cities, towns, and villages from OSM, geoBoundaries, and Esri           | ODbL 1.0             | [Divisions](https://docs.overturemaps.org/guides/divisions/)    | `id`, `names.primary`, `names.common.en`, `population`, `country`                                   | `gpkg`, `shp`        |
| **Roads**             | Road network (highways, local roads, etc.) from OSM and TomTom                                | ODbL 1.0             | [Transportation](https://docs.overturemaps.org/guides/transportation/) | `id`, `names.primary`, `names.common.en`, `class`, `subclass`, `road_surface`, `source`            | `gpkg`, `shp`        |
| **Buildings**         | Building footprints from OSM, Microsoft, Google, and Esri                                     | ODbL 1.0             | [Buildings](https://docs.overturemaps.org/guides/buildings/)    | `id`, `names.primary`, `names.common.en`, `class`, `subtype`, `height`, `level`, `num_floors`, `source` | `gpkg`, `shp`        |


### Default python example 

For default yaml example python implementation , follow [here](./example.py)

### How it works?
<img src="https://github.com/user-attachments/assets/c15e09eb-b2d2-4d05-8212-414ab097dd65" alt="overture2hdx" height="800">

### Author and License 
Kshitij Raj Sharma , License : GNU GENERAL PUBLIC LICENSE V3
