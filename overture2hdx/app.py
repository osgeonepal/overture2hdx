import concurrent.futures
import json
import logging
import os
import pathlib
import re
import shutil
import time
import zipfile
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import duckdb
import geopandas as gpd
import psutil
import requests
import yaml
from hdx.api.configuration import Configuration
from hdx.data.dataset import Dataset
from hdx.data.resource import Resource
from tqdm import tqdm

from .__version__ import __version__


# Configure logging with custom formatter
def setup_logging(level=None, format=None):
    """
    Set up logging configuration with detailed formatting.

    Args:
        level (str, optional): Logging level. Defaults to None.
        format (str, optional): Logging format. Defaults to None.
    """
    level = level or os.environ.get("LOG_LEVEL", "INFO")
    format = format or os.environ.get(
        "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )

    logging.basicConfig(level=level, format=format)

    # Add file handler to also log to a file
    file_handler = logging.FileHandler("overture2hdx.log")
    file_handler.setFormatter(logging.Formatter(format))
    logging.getLogger().addHandler(file_handler)

    # Suppress some verbose logging from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)


setup_logging()
logger = logging.getLogger(__name__)


class SystemResources:
    """Utility class to detect and manage system resources"""

    @staticmethod
    def get_memory_gb():
        """Get total system memory in GB"""
        return psutil.virtual_memory().total / (1024 * 1024 * 1024)

    @staticmethod
    def get_cpu_count():
        """Get logical CPU count"""
        return psutil.cpu_count(logical=True)

    @staticmethod
    def get_optimal_thread_count():
        """Get optimal thread count for parallel processing"""
        cpu_count = SystemResources.get_cpu_count()
        # Reserve some CPUs for system operations
        return max(1, min(cpu_count - 1, 4))

    @staticmethod
    def get_optimal_memory_limit():
        """Get optimal memory limit for DuckDB in GB"""
        mem_gb = SystemResources.get_memory_gb()
        # Use up to 70% of available memory
        return max(1, int(mem_gb * 0.7))


class Config:
    def __init__(
        self,
        config_yaml: str,
        hdx_site: str = None,
        hdx_api_key: str = None,
        hdx_owner_org: str = None,
        hdx_maintainer: str = None,
        overture_version: str = None,
        log_level: str = None,
        log_format: str = None,
        parallel_processing: bool = None,
        max_threads: int = None,
        memory_limit_gb: int = None,
    ):
        """
        Initialize the configuration.

        Args:
            config_yaml (str): YAML configuration string.
            hdx_site (str, optional): HDX site. Defaults to None.
            hdx_api_key (str, optional): HDX API key. Defaults to None.
            hdx_owner_org (str, optional): HDX owner organization. Defaults to None.
            hdx_maintainer (str, optional): HDX maintainer. Defaults to None.
            overture_version (str, optional): Overture release version. Defaults to None.
            log_level (str, optional): Logging level. Defaults to None.
            log_format (str, optional): Logging format. Defaults to None.
            parallel_processing (bool, optional): Enable parallel processing. Defaults to auto-detect.
            max_threads (int, optional): Maximum number of threads. Defaults to auto-detect.
            memory_limit_gb (int, optional): Memory limit in GB. Defaults to auto-detect.
        """
        self.HDX_SITE = hdx_site or os.environ.get("HDX_SITE") or "demo"
        self.HDX_API_KEY = hdx_api_key or os.environ.get("HDX_API_KEY")
        self.HDX_OWNER_ORG = hdx_owner_org or os.environ.get("HDX_OWNER_ORG")
        self.HDX_MAINTAINER = hdx_maintainer or os.environ.get("HDX_MAINTAINER")
        self.OVERTURE_RELEASE_VERSION = overture_version or os.environ.get("OVERTURE_VERSION", "2025-03-19.0")

        # System resources configuration
        self.PARALLEL_PROCESSING = parallel_processing if parallel_processing is not None else True
        self.MAX_THREADS = max_threads or SystemResources.get_optimal_thread_count()
        self.MEMORY_LIMIT_GB = memory_limit_gb or SystemResources.get_optimal_memory_limit()

        self.config = yaml.safe_load(config_yaml)
        self._bbox_cache = None
        self._boundary_gdf_geojson_str_cache = None

        self.validate_config()
        self.setup_config()
        setup_logging(level=log_level, format=log_format)

        # Log system configuration
        logger.info(
            f"System configuration: CPUs={SystemResources.get_cpu_count()}, "
            f"Memory={SystemResources.get_memory_gb():.1f}GB, "
            f"Using {self.MAX_THREADS} threads and {self.MEMORY_LIMIT_GB}GB memory limit"
        )

    def setup_config(self):
        """
        Set up the HDX configuration.

        Raises:
            ValueError: If HDX credentials (API key, owner org, maintainer) are not provided.
        """
        if not (self.HDX_API_KEY and self.HDX_OWNER_ORG and self.HDX_MAINTAINER):
            raise ValueError("HDX credentials (API key, owner org, maintainer) are required")

        self.HDX_URL_PREFIX = Configuration.create(
            hdx_site=self.HDX_SITE,
            hdx_key=self.HDX_API_KEY,
            user_agent="HDXPythonLibrary/6.3.4",
        )
        logger.info(f"Using HDX site: {self.HDX_URL_PREFIX}")

    def validate_config(self):
        """
        Validate the configuration.

        Raises:
            ValueError: If HDX credentials environment variables are not set.
            ValueError: If ISO3 country code is not specified in YAML configuration.
        """
        if not (self.HDX_API_KEY and self.HDX_OWNER_ORG and self.HDX_MAINTAINER):
            raise ValueError("HDX credentials environment variables not set")

        if not self.config.get("iso3"):
            raise ValueError("ISO3 country code must be specified in YAML configuration")

    @property
    def country_code(self):
        return self.config.get("iso3").upper()

    @property
    def geom(self):
        return self.config.get("geom")

    @property
    def hdx_key(self):
        return self.config.get("key")

    @property
    def hdx_subnational(self):
        return self.config.get("subnational", "false")

    @property
    def frequency(self):
        return self.config.get("frequency", "yearly")

    @property
    def categories(self):
        return self.config.get("categories", [])

    @property
    def bbox(self):
        # Use cached value if available
        if self._bbox_cache is not None:
            return self._bbox_cache

        logger.info("Calculating bounding box...")
        if self.geom:
            geom = json.loads(json.dumps(self.geom))
            boundary_gdf = gpd.GeoDataFrame.from_features(geom["features"])
            result = boundary_gdf.total_bounds.tolist()
        else:
            try:
                logger.info("Fetching bounding box from remote source...")
                bbox_response = requests.get(
                    "https://raw.githubusercontent.com/kshitijrajsharma/global-boundaries-bbox/refs/heads/main/bbox.json"
                )
                bbox_response.raise_for_status()
                bbox_data = bbox_response.json()
            except Exception as e:
                logger.error(f"Failed to fetch bbox data: {str(e)}")
                raise Exception(f"Failed to fetch bbox data: {str(e)}")

            if self.country_code not in bbox_data:
                logger.error(f"Invalid country code: {self.country_code}")
                raise ValueError(f"Invalid country code: {self.country_code}")

            result = bbox_data[self.country_code]

        # Cache the result
        self._bbox_cache = result
        logger.info(f"Bounding box: {result}")
        return result

    @property
    def boundary_gdf_geojson_str(self):
        # Use cached value if available
        if self._boundary_gdf_geojson_str_cache is not None:
            return self._boundary_gdf_geojson_str_cache

        if self.geom:
            logger.info("Generating boundary GeoJSON...")
            geom = json.loads(json.dumps(self.geom))
            boundary_gdf = gpd.GeoDataFrame.from_features(geom["features"])
            result = json.dumps(boundary_gdf.geometry.union_all().__geo_interface__)
            # Cache the result
            self._boundary_gdf_geojson_str_cache = result
            return result
        return None


class OvertureMapExporter:
    """
    A class to export map data from OvertureMaps to various formats and upload to HDX.
    Enhanced with parallel processing and performance optimizations.
    """

    def __init__(self, config: Config, duckdb_con: str = None):
        self.config = config
        self.duck_con = duckdb_con or os.environ.get("DUCKDB_CON", ":memory:")
        self.conn = duckdb.connect(self.duck_con)
        # Stats for performance monitoring
        self.stats = {
            "start_time": None,
            "end_time": None,
            "categories_processed": 0,
            "failed_categories": 0,
            "total_export_size_mb": 0,
        }

    def setup_duckdb(self, conn):
        """Configure DuckDB with optimal settings based on system resources"""
        setup_queries = [
            "INSTALL spatial",
            "INSTALL httpfs",
            "LOAD spatial",
            "LOAD httpfs",
            "SET s3_region='us-west-2'",
            f"PRAGMA memory_limit='{self.config.MEMORY_LIMIT_GB}GB'",
            f"PRAGMA threads={max(2, self.config.MAX_THREADS - 1)}",
            "PRAGMA enable_object_cache",
            "PRAGMA temp_directory='/tmp/duckdb_temp'",
        ]

        # Create temp directory if it doesn't exist
        os.makedirs("/tmp/duckdb_temp", exist_ok=True)

        for query in setup_queries:
            try:
                conn.execute(query)
                logger.debug(f"Executed DuckDB setup query: {query}")
            except Exception as e:
                logger.warning(f"Failed to execute DuckDB setup query '{query}': {str(e)}")

    def slugify(self, s):
        return re.sub(r"[^a-zA-Z0-9]+", "_", s).lower()

    def build_select_clause(self, select_fields: List[str]) -> str:
        fields = select_fields + ["geometry as geom"]
        return ",\n       ".join(fields)

    def build_where_clause(self, where_conditions: List[str]) -> str:
        bbox_conditions = f"""
            bbox.xmin >= {self.config.bbox[0]} AND
            bbox.xmax <= {self.config.bbox[2]} AND
            bbox.ymin >= {self.config.bbox[1]} AND
            bbox.ymax <= {self.config.bbox[3]}
        """

        if self.config.boundary_gdf_geojson_str:
            bbox_conditions = (
                f"({bbox_conditions}) AND ST_Intersects(geom, ST_GeomFromGeoJSON('{self.config.boundary_gdf_geojson_str}'))"
            )

        if where_conditions:
            custom_conditions = " AND ".join(f"({condition})" for condition in where_conditions)
            return f"({bbox_conditions}) AND ({custom_conditions})"

        return bbox_conditions

    def file_to_zip(self, working_dir, zip_path):
        """Optimized method to create a zip file from a directory"""
        logger.info(f"Creating zip file: {zip_path}")
        buffer_size = 4 * 1024 * 1024  # 4MB buffer for better I/O performance

        with zipfile.ZipFile(
            zip_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            allowZip64=True,
            compresslevel=1,  # Faster compression
        ) as zf:
            for file_path in pathlib.Path(working_dir).iterdir():
                logger.debug(f"Adding file to zip: {file_path}")
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                if file_size_mb > 100:  # For large files, use streaming
                    with open(file_path, "rb") as f:
                        with zf.open(file_path.name, "w", force_zip64=True) as dest:
                            shutil.copyfileobj(f, dest, buffer_size)
                else:
                    zf.write(file_path, arcname=file_path.name)

            # Add metadata
            utc_now = datetime.now(timezone.utc)
            utc_offset = utc_now.strftime("%z")
            readme_content = (
                f"Exported using overture2hdx lib : {__version__}\n"
                f"Timestamp (UTC{utc_offset}): {utc_now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Data Source: https://overturemaps.org/\n"
                f"Release: {self.config.OVERTURE_RELEASE_VERSION}\n"
                f"Country: {self.config.country_code}\n"
                f"Bounding Box: {self.config.bbox}"
            )
            zf.writestr("Readme.txt", readme_content)
            zf.writestr("config.yaml", yaml.dump(self.config.config))

        # Calculate zip size for statistics
        zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        self.stats["total_export_size_mb"] += zip_size_mb
        logger.info(f"Created zip file: {zip_path} ({zip_size_mb:.2f} MB)")

        # Clean up working directory
        shutil.rmtree(working_dir)
        return zip_path

    def cleanup(self, zip_paths):
        """Remove temporary zip files"""
        for zip_path in zip_paths:
            try:
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                    logger.debug(f"Removed temporary file: {zip_path}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {zip_path}: {str(e)}")

    def export_shapefile(self, category_conn, table_name, category_name, dir_path):
        """
        Export data to shapefile format, handling different geometry types separately.

        Args:
            category_conn: DuckDB connection
            table_name: Name of the table containing the data
            category_name: Name of the category being exported
            dir_path: Directory to save the shapefiles

        Returns:
            bool: True if export was successful
        """
        logger.info("For shapefile format, separating by geometry type")

        # Get all geometry types in the dataset
        geom_types_query = f"""
        SELECT DISTINCT ST_GeometryType(geom) as geom_type 
        FROM {table_name}
        """
        geom_types = [row[0] for row in category_conn.execute(geom_types_query).fetchall()]
        logger.info(f"Found geometry types: {', '.join(geom_types)}")

        if not geom_types:
            logger.warning("No geometry types found in data")
            return False

        # Map ST_ types to simpler names for filenames
        geom_type_mapping = {
            "ST_Point": "points",
            "ST_MultiPoint": "points",
            "ST_LineString": "lines",
            "ST_MultiLineString": "lines",
            "ST_Polygon": "polygons",
            "ST_MultiPolygon": "polygons",
        }

        # Process each geometry type separately
        exported_count = 0
        for geom_type in geom_types:
            # Get a simplified name for the geometry type
            simple_type = geom_type_mapping.get(geom_type, "other")
            export_filename = f"{dir_path}/{category_name}_{simple_type}.shp"

            logger.info(f"Exporting {geom_type} features to {export_filename}")

            export_start = time.time()
            try:
                # Export just this geometry type
                category_conn.execute(
                    f"""
                COPY (
                    SELECT * FROM {table_name}
                    WHERE ST_GeometryType(geom) = '{geom_type}'
                ) TO '{export_filename}' 
                WITH (FORMAT GDAL, SRS 'EPSG:4326', DRIVER 'ESRI Shapefile', ENCODING 'UTF-8')
                """
                )

                export_time = time.time() - export_start
                logger.info(f"Export of {simple_type} completed in {export_time:.2f}s")
                exported_count += 1
            except Exception as e:
                logger.error(f"Failed to export {geom_type}: {str(e)}")

        return exported_count > 0

    def process_category(self, category_dict) -> Tuple[str, str, List[str]]:
        """
        Process a single category and return results.

        This is designed to be run in parallel for multiple categories.
        """
        category_name = list(category_dict.keys())[0]
        category_conn = duckdb.connect(self.duck_con)
        self.setup_duckdb(category_conn)

        try:
            logger.info(f"Starting processing of category: {category_name}")
            category_config = category_dict[category_name]
            theme = category_config["theme"][0]
            feature_type = category_config["feature_type"][0]
            select_fields = category_config["select"]
            where_conditions = category_config.get("where", [])
            output_formats = category_config.get("formats", [])
            hdx = category_config.get("hdx")
            hdx_title = hdx.get("title")
            hdx_notes = hdx.get("notes", "Overturemaps Export to use in GIS applications")
            hdx_tags = hdx.get("tags", ["geodata"])
            hdx_caveats = hdx.get(
                "caveats",
                "This is verified by the community overall only but still might have some issues in individual level",
            )
            hdx_license = hdx.get(
                "license",
                "hdx-odc-odbl",
            )

            select_clause = self.build_select_clause(select_fields)
            where_clause = self.build_where_clause(where_conditions)

            # Unique table name to avoid conflicts in parallel processing
            table_name = f"{self.slugify(category_name)}_{os.getpid()}"

            query = f"""
            CREATE OR REPLACE TABLE {table_name} AS (
            SELECT
                {select_clause}
            FROM read_parquet(
                's3://overturemaps-us-west-2/release/{self.config.OVERTURE_RELEASE_VERSION}/theme={theme}/type={feature_type}/*',
                filename=true,
                hive_partitioning=1
            )
            WHERE {where_clause} )
            """

            logger.info(f"Executing DuckDB query for {category_name}")
            logger.debug(f"Query for {category_name}: {query}")

            start_time = time.time()
            category_conn.execute(query)
            query_time = time.time() - start_time

            # Check if any data was returned
            count_result = category_conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
            feature_count = count_result[0] if count_result else 0

            logger.info(f"Query for {category_name} completed in {query_time:.2f}s, found {feature_count} features")

            if feature_count == 0:
                logger.warning(f"No features found for {category_name} with the specified criteria")

            dt_name = f"{self.config.hdx_key}_{self.config.country_code.lower()}_{self.slugify(category_name)}"

            dataset_args = {
                "title": hdx_title,
                "name": dt_name,
                "notes": hdx_notes,
                "caveats": hdx_caveats,
                "private": False,
                "dataset_source": "OvertureMap",
                "methodology": "Other",
                "methodology_other": "Open Source Geographic information",
                "owner_org": self.config.HDX_OWNER_ORG,
                "maintainer": self.config.HDX_MAINTAINER,
                "subnational": self.config.hdx_subnational,
            }

            # Handle different license types
            if hdx_license == "hdx-odc-odbl":
                dataset_args["license_id"] = hdx_license
            else:
                # Custom license - use "hdx-other" and specify in "license_other"
                dataset_args["license_id"] = "hdx-other"
                dataset_args["license_other"] = hdx_license

            # Create HDX dataset
            dataset = Dataset(
                {
                    "title": hdx_title,
                    "name": dt_name,
                    "notes": hdx_notes,
                    "caveats": hdx_caveats,
                    "private": False,
                    "dataset_source": "OvertureMap",
                    "methodology": "Other",
                    "methodology_other": "Open Source Geographic information",
                    "license_id": hdx_license,
                    "owner_org": self.config.HDX_OWNER_ORG,
                    "maintainer": self.config.HDX_MAINTAINER,
                    "subnational": self.config.hdx_subnational,
                }
            )
            dataset.set_time_period(datetime.strptime(self.config.OVERTURE_RELEASE_VERSION.split(".")[0], "%Y-%m-%d"))
            dataset.set_expected_update_frequency(self.config.frequency)
            dataset.add_other_location(self.config.country_code)
            for tag in hdx_tags:
                dataset.add_tag(tag)

            logger.info(f"Creating HDX dataset for {category_name}")
            dataset.create_in_hdx(allow_no_resources=True)

            format_drivers = {
                "geojson": "GeoJSON",
                "gpkg": "GPKG",
                "shp": "ESRI Shapefile",
            }
            zip_paths = []

            # # Add a  index to improve export performance if the table is large , disabled for now as i don't see any performance improvement
            # if feature_count > 10000:
            #     try:
            #         logger.info(f"Creating index for {table_name}")
            #         category_conn.execute(f"CREATE INDEX idx_{table_name}_geom ON {table_name} (geom)")
            #     except Exception as e:
            #         logger.warning(f"Failed to create index for {table_name}: {str(e)}")

            for fmt in output_formats:
                try:
                    logger.info(f"Exporting {category_name} to {fmt} format")
                    dir_path = f"{os.getcwd()}/{category_name}_{fmt}_{os.getpid()}"
                    os.makedirs(dir_path, exist_ok=True)
                    filename = f"{dir_path}/{category_name}.{fmt}"

                    export_start = time.time()
                    if fmt == "shp":
                        # Special handling for shapefiles
                        success = self.export_shapefile(category_conn, table_name, category_name, dir_path)
                        if not success:
                            logger.error(f"Failed to export any shapefile data for {category_name}")
                            continue
                    else:
                        # Standard export for other formats
                        filename = f"{dir_path}/{category_name}.{fmt}"
                        category_conn.execute(
                            f"COPY {table_name} TO '{filename}' WITH (FORMAT GDAL, SRS 'EPSG:4326', DRIVER '{format_drivers.get(fmt)}', ENCODING 'UTF-8')"
                        )
                    export_time = time.time() - export_start

                    logger.info(f"Export to {fmt} completed in {export_time:.2f}s")

                    zip_name = f"{dt_name}_{fmt}.zip".lower()
                    zip_path = self.file_to_zip(dir_path, zip_name)
                    zip_paths.append(zip_path)

                    resource = Resource(
                        {
                            "name": zip_name,
                            "description": f"{category_name} data in {fmt.upper()} format",
                        }
                    )
                    resource.set_format(fmt)
                    resource.set_file_to_upload(zip_path)

                    logger.info(f"Adding resource to HDX dataset: {zip_name}")
                    dataset.add_update_resource(resource)
                    dataset.update_in_hdx()
                except Exception as e:
                    logger.error(f"Error exporting {category_name} to {fmt}: {str(e)}")
                    raise

            # Final update and cleanup
            dataset.update_in_hdx()
            category_conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            category_conn.close()

            logger.info(f"Successfully processed category: {category_name}")
            return category_name, "Success", zip_paths
        except Exception as e:
            logger.error(f"Error processing category {category_name}: {str(e)}", exc_info=True)
            try:
                category_conn.close()
            except:
                pass
            return category_name, f"Failed: {str(e)}", []

    def export(self) -> Dict:
        """
        Execute the export process with parallel processing and performance optimizations.
        """
        self.stats["start_time"] = time.time()
        logger.info(f"Starting export process with {len(self.config.categories)} categories")
        logger.info(f"System configuration: {self.config.MAX_THREADS} threads, {self.config.MEMORY_LIMIT_GB}GB memory limit")

        # Setup DuckDB for main connection
        self.setup_duckdb(self.conn)

        results = {}
        zip_paths_to_cleanup = []

        if self.config.PARALLEL_PROCESSING and len(self.config.categories) > 1:
            logger.info(f"Using parallel processing with {min(self.config.MAX_THREADS, len(self.config.categories))} workers")

            # Use ThreadPoolExecutor for parallel processing
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=min(self.config.MAX_THREADS, len(self.config.categories))
            ) as executor:
                future_to_category = {
                    executor.submit(self.process_category, category_dict): list(category_dict.keys())[0]
                    for category_dict in self.config.categories
                }

                for future in tqdm(
                    concurrent.futures.as_completed(future_to_category),
                    desc="Processing Categories",
                    total=len(self.config.categories),
                ):
                    category_name = future_to_category[future]
                    try:
                        name, status, paths = future.result()
                        results[name] = status
                        zip_paths_to_cleanup.extend(paths)
                        self.stats["categories_processed"] += 1
                        if "Failed" in status:
                            self.stats["failed_categories"] += 1
                    except Exception as exc:
                        logger.error(f"{category_name} generated an exception: {exc}", exc_info=True)
                        results[category_name] = f"Failed: {str(exc)}"
                        self.stats["failed_categories"] += 1
        else:
            # Sequential processing for single category or when parallel is disabled
            logger.info("Using sequential processing")
            for category_dict in tqdm(self.config.categories, desc="Categories"):
                category_name, status, paths = self.process_category(category_dict)
                results[category_name] = status
                zip_paths_to_cleanup.extend(paths)
                self.stats["categories_processed"] += 1
                if "Failed" in status:
                    self.stats["failed_categories"] += 1

        # Cleanup and close
        self.cleanup(zip_paths_to_cleanup)
        try:
            self.conn.close()
        except Exception as e:
            logger.warning(f"Error closing main DuckDB connection: {str(e)}")

        # Calculate statistics
        self.stats["end_time"] = time.time()
        elapsed_time = self.stats["end_time"] - self.stats["start_time"]
        success_count = self.stats["categories_processed"] - self.stats["failed_categories"]

        logger.info(f"Export completed in {elapsed_time:.2f}s")
        logger.info(f"Categories processed: {self.stats['categories_processed']}")
        logger.info(f"Successful: {success_count}, Failed: {self.stats['failed_categories']}")
        logger.info(f"Total export size: {self.stats['total_export_size_mb']:.2f} MB")

        return results
