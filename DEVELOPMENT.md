<p align="center">
  <a href="https://www.airflow.apache.org">
    <img alt="Airflow" src="https://cwiki.apache.org/confluence/download/attachments/145723561/airflow_transparent.png?api=v2" width="60" />
  </a>
</p>
<h1 align="center">
  Airflow Carbon Aware Provider Development
</h1>
<h3 align="center">
  Guidelines on developing and testing the Carbon Aware provider package for Apache Airflow.
</h3>

<br/>

This document provides guidelines for developing, structuring, and testing the `airflow-provider-carbonaware` package.

## Formatting Standards

### Package Name

The highest level directory for the provider package is named:

```
airflow-provider-carbonaware
```

### Repository Structure

The provider package adheres to the following general file structure:

```bash
├── LICENSE
├── README.md
├── DEVELOPMENT.md
├── carbonaware_provider # Package import directory
│   ├── __init__.py
│   ├── example_dags
│   │   └── carbonaware.py
│   │   └── carbonaware_introspection.py
│   └── operators
│       ├── __init__.py
│       └── carbonaware.py
├── pyproject.toml # Defines dependencies and package build configuration
└── tests # Unit tests for modules
    ├── __init__.py
    └── operators
        ├── __init__.py
        └── test_carbonaware_operator.py
```

## Development Standards

### Python Packaging (`pyproject.toml`)

The `pyproject.toml` file contains metadata and dependencies for the package. Key considerations:

*   **Classifiers**: Include standard Airflow provider classifiers to improve discoverability on PyPI:
    *   `Framework :: Apache Airflow`
    *   `Framework :: Apache Airflow :: Provider`
*   **Dependencies**:
    *   Ensure dependencies do not conflict with core Airflow versions. Refer to Airflow's `setup.cfg` for its dependencies.
    *   Keep dependency versions relaxed at the upper bound and specify minor versions at the lower bound (e.g., `some-package >=1.2.0, <2.0`).

### Versioning

Use standard semantic versioning (e.g., `MAJOR.MINOR.PATCH`) for releasing the package. Update the version in `carbonaware_provider/__init__.py` (which `pyproject.toml` reads dynamically) for each new release.

### Provider Metadata (`carbonaware_provider/__init__.py`)

The `get_provider_info()` method in `carbonaware_provider/__init__.py` is essential for Airflow to recognize and use the provider. It should return a dictionary with metadata like:

```python
__version__ = "0.1.0" # Example version

def get_provider_info():
    return {
        "package-name": "airflow-provider-carbonaware",  # Required
        "name": "Carbon Aware Provider",  # Required
        "description": "An Apache Airflow provider to make DAGs carbon-aware by optimizing run times based on carbon intensity.",  # Required
        "versions": [__version__],  # Required
        # Add other relevant fields like 'dependencies', 'integrations' if applicable
        "operators": [
             {
                "integration-name": "CarbonAwareScheduler", # A descriptive name for the integration your operator provides
                "python-modules": ["carbonaware_provider.operators.carbonaware.CarbonAwareOperator"],
             }
        ],
    }
```

## Documentation Standards

### Inline Module Documentation

All modules, classes, and functions should have clear docstrings explaining their purpose, arguments, and usage. This is crucial for maintainability and for auto-generated documentation.

### README

Refer to the main `README.md` for user-facing documentation, including installation, usage examples, and configuration of the `CarbonAwareOperator`.

## Functional Testing Standards

To build and test the provider locally, typically using a `.whl` file with the Astro CLI:

1.  **Clone the repository**:
    `git clone https://github.com/carbon-aware/airflow-provider-carbonaware.git`
    `cd airflow-provider-carbonaware`
2.  **Install build tools**:
    `python3 -m pip install build`
3.  **Build the wheel**:
    `python3 -m build`
    This will create a `.whl` file in the `dist/` directory (e.g., `dist/airflow_provider_carbonaware-0.1.0-py3-none-any.whl`).
4.  **Set up an Airflow Environment (e.g., using Astro CLI)**:
    *   Install the [Astro CLI](https://docs.astronomer.io/astro/cli/install-cli).
    *   Create a new Astro project: `mkdir -p astro && cd astro && astro dev init` in a new directory.
    *   Ensure your `Dockerfile` in the Astro project uses an Astro Runtime image supporting at least Airflow 2.4.0.
5.  **Install the Provider**:
    *   Copy the generated `.whl` file to your Astro project directory (`cp dist/airflow_provider_carbonaware-*.whl astro/airflow_provider_carbonaware.whl`).
    *   Add the following line to your Astro project's `Dockerfile` to install the provider:
        ```dockerfile
        COPY airflow_provider_carbonaware.whl .
        RUN pip install --user airflow_provider_carbonaware.whl
        ```
6.  **Add Example DAGs**:
    Copy the example DAGs from `carbonaware_provider/example_dags/` to the `dags/` folder of your Astro project.
7.  **Start Airflow**:
    Run `astro dev start` to build the Docker images and start Airflow locally.
8.  **Test**:
    Access the Airflow UI, enable the example DAGs, and test the `CarbonAwareOperator` functionality. Check scheduler logs for any issues.
9.  **Stop Airflow**:
    When done, run `astro dev stop`. To remove all associated Docker containers and volumes, run `astro dev kill`.

> **Note**: If you encounter issues with the Airflow webserver or scheduler, inspect the Docker logs:
> `docker ps` (to find the scheduler container ID)
> `docker logs <scheduler_container_id>`
