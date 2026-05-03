# Carolina Lake Conditions Pipeline

An end-to-end data pipeline that ingests, processes, models, and serves lake and weather condition data for downstream analysis and visualization.

## Overview

This project is designed to simulate a production-style data pipeline using a layered architecture. It ingests raw weather data, transforms it into structured datasets, stores it in DuckDB, and exposes it through a Streamlit application.

The pipeline follows a clear separation of concerns across ingestion, transformation, and consumption layers, making it easy to maintain and extend.

## Architecture

The pipeline is organized into four main layers:

- Raw: Stores unprocessed API responses
- Processed: Cleans and standardizes raw data
- Modeled: Applies transformation logic and derived fields
- Consumption: Final datasets optimized for application use

Data flows from ingestion scripts -> transformation layers -> DuckDB -> Streamlit app.

## Project Structure

    .
    ├── .github/workflows/refresh_data.yml     # Scheduled pipeline execution
    ├── app/
    │   └── streamlit_app.py                  # Frontend application
    ├── data/
    │   ├── raw/                              # Raw ingested data
    │   ├── processed/                        # Cleaned data
    │   ├── modeled/                          # Business logic applied
    │   ├── consumption/                      # Final datasets for use
    │   └── lake_conditions.duckdb            # Analytical database
    ├── notebooks/                            # Exploration and validation
    ├── src/
    │   ├── config/                           # Configuration files
    │   ├── db/
    │   │   └── load_to_duckdb.py             # Loads data into DuckDB
    │   ├── ingest/
    │   │   └── ingest_weather.py             # API ingestion logic
    │   └── transform/
    │       ├── processed_weather.py          # Raw -> processed
    │       ├── modeled_weather.py            # Processed -> modeled
    │       └── consumption_build_weather.py  # Modeled -> consumption
    ├── requirements.txt
    ├── environment.yml
    └── README.md

## Data Pipeline Flow

1. Weather data is pulled from an external API (open-meteo.com)
2. Raw data is stored in the data/raw layer
3. Transformation scripts standardize and clean the data
4. Modeled datasets apply business logic and structure
5. Final datasets are loaded into DuckDB
6. Streamlit app queries DuckDB for visualization

## How to Run

Clone the repository:

    git clone https://github.com/aowens25/carolina-lake-conditions.git
    cd carolina-lake-conditions

Install dependencies:

    pip install -r requirements.txt

Run the pipeline manually (example):

    python src/ingest/ingest_weather.py
    python src/transform/processed_weather.py
    python src/transform/modeled_weather.py
    python src/transform/consumption_build_weather.py
    python src/db/load_to_duckdb.py

Launch the application:

    streamlit run app/streamlit_app.py

## Automation

The pipeline is automated using GitHub Actions:

- refresh_data.yml triggers data refresh workflows
- Enables scheduled or event-based pipeline execution
- Simulates a production-style orchestration pattern

## Storage

DuckDB is used as the analytical database for this project. It provides a lightweight, local-first solution that supports fast querying and integrates well with Python workflows.

In a production environment, this would typically be replaced with a cloud data warehouse such as Snowflake.

## Purpose

This project demonstrates practical data engineering concepts:

- Layered data architecture
- API ingestion
- Data transformation pipelines
- Analytical database integration
- Lightweight orchestration
- Data application delivery via Streamlit

It is intended to showcase how raw external data can be transformed into a usable product for end users.

## Author

Alexander Owens