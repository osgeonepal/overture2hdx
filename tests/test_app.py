import json
import os
import sys
import time
import unittest
from unittest.mock import patch

# Add the parent directory to the path to import your package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from overture2hdx import DEFAULT_CONFIG_YAML, Config
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
        self.key = "osegonepal_pkr"
        self.subnational = True
        self.frequency = "yearly"
        self.config_yaml = DEFAULT_CONFIG_YAML.format(
            iso3=self.iso3,
            geom=self.geom,
            key=self.key,
            subnational=self.subnational,
            frequency=self.frequency,
            dataset_name=self.dataset_name,
        )

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
