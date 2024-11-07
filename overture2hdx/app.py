import json
import logging
import os
import pathlib
import re
import shutil
import zipfile
from datetime import datetime, timezone
from typing import Dict, List

import duckdb
import geopandas as gpd
import requests
import yaml
from hdx.api.configuration import Configuration
from hdx.data.dataset import Dataset
from hdx.data.resource import Resource
from hdx.utilities.easy_logging import setup_logging

from .__version__ import __version__


def setup_logging(level=None, format=None):
    level = level or os.environ.get("LOG_LEVEL", "INFO")
    format = format or os.environ.get(
        "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logging.basicConfig(level=level, format=format)


setup_logging()


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
    ):
        self.HDX_SITE = hdx_site or os.environ.get("HDX_SITE") or "demo"
        self.HDX_API_KEY = hdx_api_key or os.environ.get("HDX_API_KEY")
        self.HDX_OWNER_ORG = hdx_owner_org or os.environ.get("HDX_OWNER_ORG")
        self.HDX_MAINTAINER = hdx_maintainer or os.environ.get("HDX_MAINTAINER")
        self.OVERTURE_RELEASE_VERSION = overture_version or os.environ.get(
            "OVERTURE_VERSION", "2024-09-18.0"
        )

        self.config = yaml.safe_load(config_yaml)

        self.validate_config()

        self.setup_config()

        setup_logging(level=log_level, format=log_format)

    def setup_config(self):
        if not (self.HDX_API_KEY and self.HDX_OWNER_ORG and self.HDX_MAINTAINER):
            raise ValueError(
                "HDX credentials (API key, owner org, maintainer) are required"
            )

        self.HDX_URL_PREFIX = Configuration.create(
            hdx_site=self.HDX_SITE,
            hdx_key=self.HDX_API_KEY,
            user_agent="HDXPythonLibrary/6.3.4",
        )
        logging.info(f"Using HDX site: {self.HDX_URL_PREFIX}")

    def validate_config(self):
        if not (self.HDX_API_KEY and self.HDX_OWNER_ORG and self.HDX_MAINTAINER):
            raise ValueError("HDX credentials environment variables not set")

        if not self.config.get("iso3"):
            raise ValueError(
                "ISO3 country code must be specified in YAML configuration"
            )

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
        if self.geom:
            geom = json.loads(json.dumps(self.geom))
            boundary_gdf = gpd.GeoDataFrame.from_features(geom["features"])
            return boundary_gdf.total_bounds.tolist()
        else:
            try:
                bbox_response = requests.get(
                    "https://raw.githubusercontent.com/kshitijrajsharma/global-boundaries-bbox/refs/heads/main/bbox.json"
                )
                bbox_response.raise_for_status()
                bbox_data = bbox_response.json()
            except Exception as e:
                raise Exception(f"Failed to fetch bbox data: {str(e)}")

            if self.country_code not in bbox_data:
                raise ValueError(f"Invalid country code: {self.country_code}")

            return bbox_data[self.country_code]

    @property
    def boundary_gdf_geojson_str(self):
        if self.geom:
            geom = json.loads(json.dumps(self.geom))
            boundary_gdf = gpd.GeoDataFrame.from_features(geom["features"])
            return json.dumps(boundary_gdf.geometry.union_all().__geo_interface__)
        return None


class OvertureMapExporter:
    def __init__(self, config: Config, duckdb_con: str = None):
        self.config = config
        self.duck_con = duckdb_con or os.environ.get("DUCKDB_CON", ":memory:")
        self.conn = duckdb.connect(self.duck_con)

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
            bbox_conditions = f"({bbox_conditions}) AND ST_Intersects(geom, ST_GeomFromGeoJSON('{self.config.boundary_gdf_geojson_str}'))"

        if where_conditions:
            custom_conditions = " AND ".join(
                f"({condition})" for condition in where_conditions
            )
            return f"({bbox_conditions}) AND ({custom_conditions})"

        return bbox_conditions

    def file_to_zip(self, working_dir, zip_path):
        zf = zipfile.ZipFile(
            zip_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            allowZip64=True,
        )

        for file_path in pathlib.Path(working_dir).iterdir():
            zf.write(file_path, arcname=file_path.name)
        utc_now = datetime.now(timezone.utc)
        utc_offset = utc_now.strftime("%z")
        readme_content = f"Exported using overture2hdx lib : {__version__} , Timestamp (UTC{utc_offset}): {utc_now.strftime('%Y-%m-%d %H:%M:%S')}\n , Data Source : https://overturemaps.org/ , Release : {self.config.OVERTURE_RELEASE_VERSION}"
        zf.writestr("Readme.txt", readme_content)
        zf.writestr("config.yaml", yaml.dump(self.config.config))
        zf.close()
        shutil.rmtree(working_dir)
        return zip_path

    def cleanup(self, zip_paths):
        for zip_path in zip_paths:
            os.remove(zip_path)

    def export(self) -> Dict:
        setup_queries = [
            "INSTALL spatial",
            "INSTALL httpfs",
            "LOAD spatial",
            "LOAD httpfs",
            "SET s3_region='us-west-2'",
        ]

        for query in setup_queries:
            self.conn.execute(query)

        results = {}
        for category_dict in self.config.categories:
            category_name = list(category_dict.keys())[0]
            logging.info(f"Processing {category_name}")
            category_config = category_dict[category_name]
            theme = category_config["theme"][0]
            feature_type = category_config["feature_type"][0]
            select_fields = category_config["select"]
            where_conditions = category_config.get("where", [])
            output_formats = category_config.get("formats", [])
            hdx = category_config.get("hdx")
            hdx_title = hdx.get("title")
            hdx_notes = hdx.get(
                "notes", "Overturemaps Export to use in GIS applications"
            )
            hdx_tags = hdx.get("tags", ["geodata"])
            hdx_caveats = hdx.get(
                "caveats",
                "This is verified by the community overall only but still might have some issues in individual level",
            )

            select_clause = self.build_select_clause(select_fields)
            where_clause = self.build_where_clause(where_conditions)

            query = f"""
            CREATE OR REPLACE TABLE {category_name} AS (
            SELECT
                {select_clause}
            FROM read_parquet(
                's3://overturemaps-us-west-2/release/{self.config.OVERTURE_RELEASE_VERSION}/theme={theme}/type={feature_type}/*',
                filename=true,
                hive_partitioning=1
            )
            WHERE {where_clause} )
            """
            logging.info(query)

            dataset = Dataset(
                {
                    "title": hdx_title,
                    "name": f"{self.config.hdx_key}_{self.config.country_code.lower()}_{self.slugify(category_name)}",
                    "notes": hdx_notes,
                    "caveats": hdx_caveats,
                    "private": False,
                    "dataset_source": "OvertureMap",
                    "methodology": "Other",
                    "methodology_other": "Open Source Geographic information",
                    "license_id": "hdx-odc-odbl",
                    "owner_org": self.config.HDX_OWNER_ORG,
                    "maintainer": self.config.HDX_MAINTAINER,
                    "subnational": self.config.hdx_subnational,
                }
            )
            dataset.set_time_period(
                datetime.strptime(
                    self.config.OVERTURE_RELEASE_VERSION.split(".")[0], "%Y-%m-%d"
                )
            )
            dataset.set_expected_update_frequency(self.config.frequency)
            dataset.add_other_location(self.config.country_code)
            for tag in hdx_tags:
                dataset.add_tag(tag)
            dataset.create_in_hdx(allow_no_resources=True)

            self.conn.execute(query)
            format_drivers = {
                "geojson": "GeoJSON",
                "gpkg": "GPKG",
                "shp": "ESRI Shapefile",
            }
            zip_paths = []

            for fmt in output_formats:
                dir_path = f"{os.getcwd()}/{category_name}_{fmt}"
                os.makedirs(dir_path, exist_ok=True)
                filename = f"{dir_path}/{category_name}.{fmt}"

                logging.info(f"Exporting {category_name} to {fmt} format")

                self.conn.execute(
                    f"COPY {category_name} TO '{filename}' WITH (FORMAT GDAL,SRS 'EPSG:4326', DRIVER '{format_drivers.get(fmt)}')"
                )
                zip_name = (
                    f"{self.config.country_code}_{category_name}_{fmt}.zip".lower()
                )
                zip_path = self.file_to_zip(dir_path, zip_name)
                zip_paths.append(zip_path)
                resource = Resource(
                    {
                        "name": zip_name,
                        "description": fmt,
                    }
                )
                resource.set_format(fmt)
                resource.set_file_to_upload(zip_path)
                dataset.add_update_resource(resource)
                dataset.update_in_hdx()

            results[category_name] = "Success"
            dataset.update_in_hdx()
            self.cleanup(zip_paths)
            self.conn.execute(f"DROP TABLE IF EXISTS {category_name}")

        self.conn.close()
        return results


if __name__ == "__main__":

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
            title: Roads of Pokhara
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
    """

    try:
        config = Config(
            config_yaml=config_yaml_mini,
            log_level="DEBUG",
            log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        exporter = OvertureMapExporter(config)
        results = exporter.export()
        logging.info(results)
    except Exception as e:
        logging.error(f"Error: {str(e)}")
