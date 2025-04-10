from .app import Config
from .app import OvertureMapExporter as Exporter

DEFAULT_CONFIG_YAML = """
iso3: {iso3}
geom: {geom}
key: {key}
subnational: {subnational}
frequency: {frequency}
dataset_name: {dataset_name}
categories:

- Hospitals:
    select:
        - id
        - names.primary AS name
        - names.common->'en' as name_en
        - categories.primary AS category
        - addresses[1].freeform AS address
        - phones[1] AS phone
        - emails[1] AS email
        - websites[1] AS website
        - confidence
        - sources[1].dataset AS source
    hdx:

        notes: This dataset includes health points of interest (e.g., hospitals and clinics) from the Overture Places theme, derived from open data provided by Meta and Microsoft. Useful for public health logistics and emergency response. Read more at https://docs.overturemaps.org/guides/places/
        tags:
        - health
        license: CDLA Permissive 2.0
        license_url: https://cdla.dev/permissive-2-0/
        caveats: Contains hospital locations from the Overture Places theme, derived from Meta and Microsoft data. Licensed under CDLA Permissive 2.0. Data might contain errors and was processed and published using the Overture public release via the overture2hdx package.
    theme:
        - places
    feature_type:
        - place
    where:
        - "categories.primary IN ('hospital', 'clinic')"
    formats:
        - gpkg
        - shp

- Schools:
    select:
        - id
        - names.primary AS name
        - names.common->'en' as name_en
        - categories.primary AS category
        - addresses[1].freeform AS address
        - phones[1] AS phone
        - websites[1] AS website
        - confidence
        - sources[1].dataset AS source
    hdx:
        notes: This dataset captures educational points of interest (e.g., schools and universities) from the Overture Places theme, using Meta and Microsoft open data. Read more at https://docs.overturemaps.org/guides/places/
        tags:
        - education
        license: CDLA Permissive 2.0
        license_url: https://cdla.dev/permissive-2-0/
        caveats: Contains school points of interest from Meta and Microsoft via Overture Places. Licensed under CDLA Permissive 2.0. Data might contain errors and was processed and published using the Overture public release via the overture2hdx package.
    theme:
        - places
    feature_type:
        - place
    where:
        - "categories.primary IN ('school', 'university')"
    formats:
        - gpkg
        - shp

- Rivers:
    select:
        - id
        - names.primary AS name
        - names.common->'en' as name_en
        - subtype
        - class
        - is_salt
        - wikidata
        - sources[1].dataset AS source
    hdx:
        notes: This dataset contains rivers, lakes, and other water features from the Overture Base theme, primarily sourced from OpenStreetMap. Read more at https://docs.overturemaps.org/guides/base/
        tags:
        - environment
        license: ODbL 1.0
        caveats: Includes OpenStreetMap-derived hydrography under the Open Database License (ODbL). Share-alike and attribution are required. Data might contain errors and was processed and published using the Overture public release via the overture2hdx package.
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
        - names.primary AS name
        - names.common->'en' as name_en
        - subtype
        - class
        - surface
        - wikidata
        - sources[1].dataset AS source
    hdx:
        notes: This dataset covers land use polygons (e.g., farmland, forests) from the Overture Base theme, derived primarily from OpenStreetMap landuse tags. Read more at https://docs.overturemaps.org/guides/base/
        tags:
        - environment
        license: ODbL 1.0
        caveats: Contains land use data derived from OpenStreetMap. Distributed under ODbL v1.0. Attribution and share-alike are required. Data might contain errors and was processed and published using the Overture public release via the overture2hdx package.
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
        - names.primary AS name
        - names.common->'en' as name_en
        - categories.primary AS category
        - addresses[1].freeform AS address
        - phones[1] AS phone
        - websites[1] AS website
        - confidence
        - sources[1].dataset AS source
    hdx:
        notes: This dataset includes airports, train stations, and terminals from the Overture Places theme, derived from Meta and Microsoft open data. Read more at https://docs.overturemaps.org/guides/places/
        tags:
        - transportation
        - logistics
        license: CDLA Permissive 2.0
        license_url: https://cdla.dev/permissive-2-0/
        caveats: Contains transportation points of interest (e.g., airports, stations) from Meta and Microsoft via Overture Places. Licensed under CDLA Permissive 2.0. Data might contain errors and was processed and published using the Overture public release via the overture2hdx package.
    theme:
        - places
    feature_type:
        - place
    where:
        - "categories.primary IN ('airport', 'train_station', 'bus_station', 'light_rail_and_subway_station', 'ferry_terminal')"
    formats:
        - gpkg
        - shp

- Settlements:
    select:
        - id
        - names.primary AS name
        - names.common->'en' as name_en
        - population
        - region
        - wikidata
        - sources[1].dataset AS source
    hdx:
        notes: This dataset includes populated places (cities, towns, villages, hamlets) from the Overture Divisions theme, which merges boundaries from OpenStreetMap, geoBoundaries, and Esri. Read more at https://docs.overturemaps.org/guides/divisions/
        tags:
        - population
        license: ODbL 1.0
        caveats: Includes settlement-level boundaries from OSM (ODbL), geoBoundaries (CC BY), and Esri (CC BY). Final dataset is ODbL-licensed. Share-alike and attribution required. Data might contain errors and was processed and published using the Overture public release via the overture2hdx package.
    theme:
        - divisions
    feature_type:
        - division
    where:
        - "subtype = 'locality'"
    formats:
        - gpkg
        - shp

- Roads:
    select:
        - id
        - names.primary AS name
        - names.common->'en' as name_en
        - class
        - subclass
        - subtype
        - road_surface[1].value as road_surface
        - sources[1].dataset AS source
    hdx:
        notes: This dataset includes road networks (e.g., highways, local roads) from the Overture Transportation theme, sourced from OpenStreetMap and TomTom. Read more at https://docs.overturemaps.org/guides/transportation/
        tags:
        - geodata
        - transportation
        - roads
        license: ODbL 1.0
        caveats: Contains roads from OSM and TomTom via Overture. Licensed under ODbL v1.0. Attribution and share-alike required. Data might contain errors and was processed and published using the Overture public release via the overture2hdx package.
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
        - names.primary AS name
        - names.common->'en' as name_en
        - class
        - subtype
        - height
        - level
        - num_floors
        - num_floors_underground 
        - is_underground
        - has_parts
        - roof_material
        - roof_shape
        - roof_color
        - sources[1].dataset AS source
    hdx:
        notes: This dataset includes building footprints from the Overture Buildings theme. Sources include OSM, Microsoft Global ML Buildings, Google Open Buildings, and Esri Community Maps. Read more at https://docs.overturemaps.org/guides/buildings/
        tags:
        - geodata
        - buildings
        - infrastructure
        license: ODbL 1.0
        caveats: Includes building data from OSM (ODbL), Microsoft (ODbL), Google (CC BY), and Esri (CC BY). Final dataset is ODbL-licensed. Attribution and share-alike required. Data might contain errors and was processed and published using the Overture public release via the overture2hdx package.
    theme:
        - buildings
    feature_type:
        - building
    formats:
        - gpkg
        - shp
"""
