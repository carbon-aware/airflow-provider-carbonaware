__version__ = "0.2.0"


## This is needed to allow Airflow to pick up specific metadata fields it needs for certain features.
def get_provider_info():
    return {
        "package-name": "airflow-provider-carbonaware",  # Required
        "name": "CarbonAware",  # Required
        "description": "An Apache Airflow provider for CarbonAware.",  # Required
        "connection-types": [],
        "extra-links": [
            "airflow_provider_carbonaware.operators.carbonaware.CarbonAwareOperatorExtraLink"
        ],
        "versions": [__version__],  # Required
    }
