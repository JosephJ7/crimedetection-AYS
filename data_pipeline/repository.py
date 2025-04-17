from dagster import Definitions

from project_master import combined_pipeline_job 
from dagster_pipe import data_pipeline  

defs = Definitions(
    jobs=[data_pipeline, combined_pipeline_job],
    schedules=[],
    sensors=[],
)
