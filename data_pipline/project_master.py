from dagster  import job
from data_pipline.dagster_pipe import data_pipeline  

# List of dataset configurations
dataset_configs = [
    {
        "url": "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/CJQ06/JSON-stat/2.0/en",
        "table_name": "crime_offence_garda"
    },
    {
        "url": "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/RCD09/JSON-stat/2.0/en",
        "table_name": "crime_offence_age"
    }
]


def project_master():
    # Run the pipeline for each dataset
    for config in dataset_configs:
        run_config = {
            "ops": {
                "fetch_and_store_data": {
                    "config": {
                        "url": config["url"],
                        "table_name": config["table_name"]
                    }
                },
                "transform_and_store": {
                    "config": {
                        "table_name": config["table_name"]
                    }
                },
                "visualize": {
                    "config": {
                        "table_name": config["table_name"]
                    }
                }
            }
        }

        result = data_pipeline.execute_in_process(run_config=run_config)
        print(f"Pipeline run for {config['table_name']} was {'successful' if result.success else 'unsuccessful'}")


if __name__ == "__main__":
    project_master()