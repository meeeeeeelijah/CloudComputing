# Cloud-Native Nutritional Insights

A Python data-analysis application for the Cloud-Native Nutritional Insights project. The application analyzes the `All_Diets.csv` recipe dataset and calculates nutritional insights by diet type and cuisine.

## Current scope

This repository currently implements **Task 1: Dataset Analysis and Insights**.

The analysis:

- Cleans missing and invalid nutritional values.
- Calculates average protein, carbohydrates, and fat by diet type.
- Identifies the five most protein-rich recipes for each diet type.
- Identifies the diet type with the highest average protein content.
- Finds the most common cuisine for each diet type.
- Calculates protein-to-carbohydrate and carbohydrate-to-fat ratios.
- Generates bar charts, heatmaps, and scatter plots.

Tasks involving Docker, serverless processing, and CI/CD will be added as the project progresses.

## Requirements

- Python 3.10 or later
- Pandas
- Matplotlib
- Seaborn

## Project structure

```text
.
├── All_Diets.csv
├── data_analysis.py
├── requirements.txt
├── outputs/
├── README.md
└── .gitignore
