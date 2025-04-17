from dagster import graph, job, ConfigMapping
from data_pipeline.dagster_pipe import data_pipeline  # your @job

presets_config = {
    "crime_offence_garda": {
        "ops": {
            "fetch_and_store_data": {
                "config": {
                    "url": "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/CJQ06/JSON-stat/2.0/en",
                    "table_name": "crime_offence_garda"
                }
            },
            "transform_and_store": {
                "config": {
                    "table_name": "crime_offence_garda"
                }
            },
            "visualize": {
                "config": {
                    "table_name": "crime_offence_garda"
                }
            }
        }
    },
    "crime_offence_age": {
        "ops": {
            "fetch_and_store_data": {
                "config": {
                    "url": "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/RCD09/JSON-stat/2.0/en",
                    "table_name": "crime_offence_age"
                }
            },
            "transform_and_store": {
                "config": {
                    "table_name": "crime_offence_age"
                }
            },
            "visualize": {
                "config": {
                    "table_name": "crime_offence_age"
                }
            }
        }
    }
}



@graph
def full_pipeline():
    data_pipeline.alias("crime_offence_garda")()
    data_pipeline.alias("crime_offence_age")()
    


@job(config=ConfigMapping(
    config_fn=lambda cfg: {
        "ops": {
            "full_pipeline": {
                "ops": {
                    "crime_offence_garda": presets_config["crime_offence_garda"],
                    "crime_offence_age": presets_config["crime_offence_age"],
                }
            }
        }
        
    }
))
def combined_pipeline_job():
    full_pipeline()