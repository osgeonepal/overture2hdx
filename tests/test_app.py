import json
import os
import sys
import time
import unittest
from unittest.mock import patch

# Add the parent directory to the path to import your package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from overture2hdx import Config
from overture2hdx import Exporter as OvertureMapExporter


class TestRealExport(unittest.TestCase):
    """Test real data export from Overture Maps."""

    def setUp(self):
        """Set up test environment with sample configuration."""
        # Test geometry for Pokhara, Nepal
        self.geom = json.dumps(
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
        self.iso3 = "NPL"
        self.dataset_name = "Pokhara, Nepal"
        self.key = "osegonepal_pkr_"
        self.subnational = True
        self.frequency = "yearly"
        self.config_yaml = f"""
        iso3: {self.iso3}
        geom: {self.geom}
        key: {self.key}
        subnational: {self.subnational}
        frequency: {self.frequency}
        categories:

        - Hospitals:
            select:
                - id
                - names.primary as name
                - names.common.en as name_en
                - categories.primary as category
            hdx:
                title: Hospitals of {self.dataset_name}
                notes: This dataset includes health POIs (e.g., hospitals and clinics) from the Overture Places theme, derived from open data provided by Meta and Microsoft. Useful for public health logistics and emergency response. Read More, https://docs.overturemaps.org/guides/places/
                tags:
                - health
                license: CDLA Permissive 2.0
                caveats: Contains hospital locations from the Overture Places theme, derived from Meta and Microsoft data. Licensed under CDLA Permissive 2.0. Data might contain errors and was scraped and published using the Overture public release via the overture2hdx package.
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
                - names.primary as name
                - names.common.en as name_en
                - categories.primary as category
            hdx:
                title: Schools of {self.dataset_name}
                notes: This dataset captures education POIs (e.g., schools and universities) from the Overture Places theme, using Meta and Microsoft open data. Read More, https://docs.overturemaps.org/guides/places/
                tags:
                - education
                license: CDLA Permissive 2.0
                caveats: Contains school POIs from Meta and Microsoft via Overture Places. Licensed under CDLA Permissive 2.0. Data might contain errors and was scraped and published using the Overture public release via the overture2hdx package.
            theme:
                - places
            feature_type:
                - place
            where:
                - "categories.primary IN ('hospital', 'clinic')"
            formats:
                - gpkg
                - shp

        - Rivers:
            select:
                - id
                - names.primary as name
                - names.common.en as name_en
                - subtype
                - class
            hdx:
                title: Rivers of {self.dataset_name}
                notes: This dataset contains rivers, lakes, and other water features from the Overture Base theme, primarily sourced from OpenStreetMap. Read More, https://docs.overturemaps.org/guides/base/
                tags:
                - environment
                license: ODbL 1.0
                caveats: Includes OpenStreetMap-derived hydrography under the Open Database License (ODbL). Share-alike and attribution are required. Data might contain errors and was scraped and published using the Overture public release via the overture2hdx package.
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
                - names.common.en as name_en
                - subtype
                - class
            hdx:
                title: Land Use of {self.dataset_name}
                notes: This dataset covers land use polygons (e.g., farmland, forests) from the Overture Base theme, derived primarily from OpenStreetMap landuse tags. Read More, https://docs.overturemaps.org/guides/base/
                tags:
                - environment
                license: ODbL 1.0
                caveats: Contains land use data derived from OpenStreetMap. Distributed under ODbL v1.0. Attribution and share-alike are required. Data might contain errors and was scraped and published using the Overture public release via the overture2hdx package.
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
                - names.common.en as name_en
                - categories.primary as category
            hdx:
                title: Transportation Hubs of {self.dataset_name}
                notes: This dataset includes airports, train stations, and terminals from the Overture Places theme, derived from Meta and Microsoft open data. Read More, https://docs.overturemaps.org/guides/places/
                tags:
                - transportation
                - logistics
                license: CDLA Permissive 2.0
                caveats: Contains transportation POIs (e.g., airports, stations) from Meta and Microsoft via Overture Places. Licensed under CDLA Permissive 2.0. Data might contain errors and was scraped and published using the Overture public release via the overture2hdx package.
            theme:
                - base
            feature_type:
                - land_use
            formats:
                - gpkg
                - shp

                
        - Settlements:
            select:
                - id
                - names.primary as name
                - names.common.en as name_en
                - population
                - country
            hdx:
                title: Settlements of {self.dataset_name}
                notes: This dataset includes populated places (cities, towns, villages, hamlets) from the Overture Divisions theme, which merges boundaries from OpenStreetMap, geoBoundaries, and Esri. Read More, https://docs.overturemaps.org/guides/divisions/
                tags:
                - population
                license: ODbL 1.0
                caveats: Includes settlement-level boundaries from OSM (ODbL), geoBoundaries (CC BY), and Esri (CC BY). Final dataset is ODbL-licensed. Share-alike and attribution required. Data might contain errors and was scraped and published using the Overture public release via the overture2hdx package.
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
                - names.primary as name
                - names.common.en as name_en
                - class as class
                - subclass as subclass
                - UNNEST(JSON_EXTRACT(road_surface, '$[*].value')) as road_surface
                - UNNEST(JSON_EXTRACT(sources, '$[*].dataset')) AS source
            hdx:
                title: Roads of {self.dataset_name}
                notes: This dataset includes road networks (e.g., highways, local roads) from the Overture Transportation theme, sourced from OpenStreetMap and TomTom. Read More, https://docs.overturemaps.org/guides/transportation/
                tags:
                - geodata
                - transportation
                - roads
                license: ODbL 1.0
                caveats: Contains roads from OSM and TomTom via Overture. Licensed under ODbL v1.0. Attribution and share-alike required. Data might contain errors and was scraped and published using the Overture public release via the overture2hdx package.

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
                - names.common.en as name_en
                - class as class
                - subtype as subtype
                - height as height
                - level as level
                - num_floors as num_floors
                - UNNEST(JSON_EXTRACT(sources, '$[*].dataset')) AS source
            hdx:
                title: Buildings of {self.dataset_name}
                notes: This dataset includes building footprints from the Overture Buildings theme. Sources include OSM, Microsoft Global ML Buildings, Google Open Buildings, and Esri Community Maps. Read More, https://docs.overturemaps.org/guides/buildings/
                tags:
                - geodata
                - buildings
                - infrastructure
                license: ODbL 1.0
                caveats: Includes building data from OSM (ODbL), Microsoft (ODbL), Google (CC BY), and Esri (CC BY). Final dataset is ODbL-licensed. Attribution and share-alike required. Data might contain errors and was scraped and published using the Overture public release via the overture2hdx package.
            theme:
                - buildings
            feature_type:
                - building
            formats:
                - gpkg
                - shp

        """

        # Set environment variables
        os.environ["HDX_SITE"] = "demo"
        os.environ["HDX_API_KEY"] = "test-api-key"
        os.environ["HDX_OWNER_ORG"] = "test-org"
        os.environ["HDX_MAINTAINER"] = "test-maintainer"

        # Create test output directory
        self.test_output_dir = os.path.join(os.getcwd(), "test_output")
        os.makedirs(self.test_output_dir, exist_ok=True)
        os.chdir(self.test_output_dir)

    def tearDown(self):
        """Clean up after tests."""
        # Clean up test output directory
        if os.path.exists(self.test_output_dir):
            for file in os.listdir(self.test_output_dir):
                try:
                    if file.endswith(".zip") or file.endswith(".log"):
                        os.remove(os.path.join(self.test_output_dir, file))
                except Exception as e:
                    print(f"Error removing file {file}: {e}")

    @patch("hdx.data.dataset.Dataset.create_in_hdx")
    @patch("hdx.data.dataset.Dataset.update_in_hdx")
    def test_real_export(self, mock_update_hdx, mock_create_hdx):
        """Test a real export from Overture Maps."""
        # Skip HDX upload by mocking the HDX functions
        mock_create_hdx.return_value = True
        mock_update_hdx.return_value = True

        print(f"\nStarting real export test at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Using test output directory: {self.test_output_dir}")

        # Create configuration
        config = Config(config_yaml=self.config_yaml, overture_version="2025-03-19.0")  # Use a specific version for testing

        # Create exporter with reduced memory and thread settings for testing
        exporter = OvertureMapExporter(config)

        # Set a lower memory limit for testing
        exporter.config.MEMORY_LIMIT_GB = min(exporter.config.MEMORY_LIMIT_GB, 4)
        exporter.config.MAX_THREADS = min(exporter.config.MAX_THREADS, 2)

        print(f"System resources: {exporter.config.MAX_THREADS} threads, {exporter.config.MEMORY_LIMIT_GB}GB memory")

        # Start timing
        start_time = time.time()

        # Run the export
        results = exporter.export()

        # End timing
        end_time = time.time()
        duration = end_time - start_time

        # Print results
        print(f"\nExport completed in {duration:.2f} seconds")
        print(f"Export results: {results}")
        print(f"Stats: {exporter.stats}")

        # Assertions
        self.assertEqual(exporter.stats["categories_processed"], 8)
        self.assertEqual(exporter.stats["failed_categories"], 0)


if __name__ == "__main__":
    unittest.main()
