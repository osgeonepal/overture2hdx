# Usage

## Requirements

- Python 3.7 +

## Installation 

```bash
pip install overture2hdx
```

## Configuration 

Configuration can be created from yaml file , Refer to configuration section for more 

sample : 
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

## Usage 
```python 
from overture2hdx import Config, Exporter

config = Config(config_yaml=config_yaml_mini)
exporter = Exporter(config)
results = exporter.export()
print(results)
```