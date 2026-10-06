## Current project status

Tasks 1–3 are implemented. Task 4 covers the GitHub Actions CI/CD pipeline, and Task 5 covers enhancement research and implementation. These will be documented when completed.

## Requirements

### Task 1 and Task 2

- Python 3.9 or later
- Docker Desktop
- Docker Compose
- pandas
- Matplotlib
- Seaborn

The Dockerfile installs the Python packages required to run the data analysis application.

### Task 3

- Azure Functions Core Tools
- Azurite
- Azure Storage Blob SDK
- Azure Functions Python library

Azure and serverless dependencies are listed in `requirements.txt`.

## Project structure

```text
.
├── data/
│   └── All_Diets.csv
├── outputs/
│   ├── CSV analysis results
│   └── PNG visualizations
├── serverless/
│   ├── upload_data.py
│   └── database/
│       └── diet_results.json
├── data_analysis.py
├── function_app.py
├── Dockerfile
├── compose.yml
├── host.json
├── requirements.txt
├── README.md
└── .gitignore
