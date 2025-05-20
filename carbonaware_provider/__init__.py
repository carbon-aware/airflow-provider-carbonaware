__version__ = "1.0.0"

## This is needed to allow Airflow to pick up specific metadata fields it needs for certain features.
def get_provider_info():
    return {
        "package-name": "airflow-provider-carbon-aware",  # Required
        "name": "CarbonAware",  # Required
        "description": "An Apache Airflow provider for CarbonAware.",  # Required
        "connection-types": [
            {
                "connection-type": "carbon-aware",
                "hook-class-name": "carbonaware_provider.hooks.carbonaware.CarbonAwareHook"
            }
        ],
        "extra-links": ["carbonaware_provider.operators.carbonaware.CarbonAwareOperatorExtraLink"],
        "versions": [__version__],  # Required
    }
