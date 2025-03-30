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
        self.test_geom = json.dumps(
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
        geom: {self.test_geom}
        key: {self.key}
        subnational: {self.subnational}
        frequency: {self.frequency}
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
                title: Roads of {self.dataset_name}
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
                title: Buildings of {self.dataset_name}
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
                title: Healthcare Facilities of {self.dataset_name}
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
                title: Educational Facilities of {self.dataset_name}
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
                title: Water Bodies of {self.dataset_name}
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
                title: Land Use of {self.dataset_name}
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
                title: Transportation Hubs of {self.dataset_name}
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
                title: Settlements of {self.dataset_name}
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

        # Check if files were created
        zip_files = [f for f in os.listdir(self.test_output_dir) if f.endswith(".zip")]
        print(f"Generated zip files: {zip_files}")

        # Assertions
        self.assertEqual(exporter.stats["categories_processed"], 8)
        self.assertEqual(exporter.stats["failed_categories"], 0)
        self.assertTrue(len(zip_files) > 0, "No zip files were created")

        # Verify zip file contents
        if len(zip_files) > 0:
            import zipfile

            zip_path = os.path.join(self.test_output_dir, zip_files[0])
            self.assertTrue(os.path.exists(zip_path), f"Zip file {zip_path} does not exist")

            # Check zip file size
            file_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
            print(f"Zip file size: {file_size_mb:.2f} MB")

            # Check zip file contents
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                file_list = zip_ref.namelist()
                print(f"Zip file contents: {file_list}")

                # Check that there's at least one data file
                data_files = [f for f in file_list if f.endswith(".gpkg")]
                self.assertTrue(len(data_files) > 0, "No data files in zip")

                # Check readme exists
                self.assertIn("Readme.txt", file_list, "No Readme.txt in zip")

                # Optional: Examine file contents
                if "Readme.txt" in file_list:
                    with zip_ref.open("Readme.txt") as readme:
                        readme_content = readme.read().decode("utf-8")
                        print(f"Readme content: {readme_content[:200]}...")
                        self.assertIn("Overturemaps", readme_content)


if __name__ == "__main__":
    unittest.main()
