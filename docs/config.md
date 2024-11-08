# Configuration

The application is configured using a YAML file and environment variables.

## YAML Configuration


### YAML Fields

- **iso3**: The ISO3 country code. This is a required field.
- **geom**: The geometry in GeoJSON format. This is used to define the area of interest.
- **key**: A unique key for the dataset.
- **subnational**: A boolean indicating whether the data is subnational.
- **frequency**: The update frequency of the dataset (e.g., yearly, monthly).
- **categories**: A list of categories to be exported. Each category contains:
  - **select**: A list of fields to select from the data.
  - **hdx**: HDX-specific metadata including:
    - **title**: The title of the dataset.
    - **notes**: Notes or description of the dataset.
    - **tags**: A list of tags for the dataset.
  - **theme**: The theme of the data (e.g., transportation).
  - **feature_type**: The type of features to export (e.g., segment).
  - **formats**: A list of formats to export the data in (e.g., gpkg, shp).

## Environment Variables

The application uses several environment variables to configure its behavior. Below is a list of the environment variables and their descriptions:

### HDX_SITE

- **Description**: The HDX site to use.
- **Default**: `demo`
- **Example**: `export HDX_SITE=prod`

### HDX_API_KEY

- **Description**: The API key for accessing HDX.
- **Required**: Yes
- **Example**: `export HDX_API_KEY=your_hdx_api_key`

### HDX_OWNER_ORG

- **Description**: The owner organization on HDX.
- **Required**: Yes
- **Example**: `export HDX_OWNER_ORG=your_hdx_owner_org`

### HDX_MAINTAINER

- **Description**: The maintainer for the dataset on HDX.
- **Required**: Yes
- **Example**: `export HDX_MAINTAINER=your_hdx_maintainer`

### OVERTURE_VERSION

- **Description**: The release version of Overture data.
- **Default**: `2024-09-18.0`
- **Example**: `export OVERTURE_VERSION=2024-09-18.0`

### LOG_LEVEL

- **Description**: The logging level.
- **Default**: `INFO`
- **Example**: `export LOG_LEVEL=DEBUG`

### LOG_FORMAT

- **Description**: The logging format.
- **Default**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- **Example**: `export LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"`

### DUCKDB_CON

- **Description**: The DuckDB connection string.
- **Default**: `:memory:`
- **Example**: `export DUCKDB_CON=your_duckdb_connection_string`

## Example : 

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

```
