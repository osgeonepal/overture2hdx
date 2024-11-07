# Overture Map Exporter

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
geom: '{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": {"coordinates": [[[83.98047393581618, 28.255338988044088], [83.973540694181, 28.230486421513703], [83.91927014759125, 28.214265947308945], [83.97832224013575, 28.195093119231174], [83.96971545741735, 28.158212628626416], [84.00175181531534, 28.19361814379657], [84.03187555483152, 28.168540447741847], [84.01059767533235, 28.208788347541898], [84.0342663278089, 28.255549578267903], [83.99960011963498, 28.228801292171724], [83.98047393581618, 28.255338988044088]]], "type": "Polygon"}}]}'
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
from overture2hdx import Config, OvertureMapExporter
config = Config(
    config_yaml=config_yaml_mini,
    log_level="DEBUG",
    log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
exporter = OvertureMapExporter(config)
results = exporter.export()
logging.info(results)
```

### Author and License 
Kshitij Raj Sharma , License : GNU GENERAL PUBLIC LICENSE V3