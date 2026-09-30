from pathlib import Path

import matplotlib

# Required for computers and servers without a graphical desktop.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


INPUT_FILE = Path("All_Diets.csv")
OUTPUT_DIR = Path("outputs")

OUTPUT_DIR.mkdir(exist_ok=True)
sns.set_theme(style="whitegrid")


def find_column(dataframe, *possible_names):
    """Find a column while allowing minor naming differences."""
    normalized_columns = {
        column.strip().lower().replace(" ", "").replace("_", ""): column
        for column in dataframe.columns
    }

    for name in possible_names:
        normalized_name = name.lower().replace(" ", "").replace("_", "")

        if normalized_name in normalized_columns:
            return normalized_columns[normalized_name]

    raise KeyError(
        f"Could not find any of these columns: {possible_names}\n"
        f"Available columns: {list(dataframe.columns)}"
    )


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_FILE}. "
            "Place All_Diets.csv beside data_analysis.py."
        )

    # Load the dataset.
    df = pd.read_csv(INPUT_FILE)

    # Find the dataset columns.
    diet_column = find_column(df, "Diet_type", "Diet Type")
    recipe_column = find_column(df, "Recipe_name", "Recipe Name")
    cuisine_column = find_column(df, "Cuisine_type", "Cuisine Type")
    protein_column = find_column(df, "Protein(g)", "Protein (g)", "Protein")
    carbs_column = find_column(df, "Carbs(g)", "Carbs (g)", "Carbs")
    fat_column = find_column(df, "Fat(g)", "Fat (g)", "Fat")

    # Rename columns to consistent internal names.
    df = df.rename(
        columns={
            diet_column: "Diet_type",
            recipe_column: "Recipe_name",
            cuisine_column: "Cuisine_type",
            protein_column: "Protein_g",
            carbs_column: "Carbs_g",
            fat_column: "Fat_g",
        }
    )

    numeric_columns = ["Protein_g", "Carbs_g", "Fat_g"]
    text_columns = ["Diet_type", "Recipe_name", "Cuisine_type"]

    # Convert nutritional columns to numeric values.
    # Invalid values become missing values.
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # Remove surrounding whitespace from text fields.
    for column in text_columns:
        df[column] = df[column].astype("string").str.strip()
        df[column] = df[column].replace("", pd.NA)

    print("Original rows:", len(df))

    print("\nMissing values before cleaning:")
    print(df[numeric_columns + text_columns].isna().sum())

    # Replace missing nutritional values with each column's mean.
    for column in numeric_columns:
        column_mean = df[column].mean()

        if pd.isna(column_mean):
            raise ValueError(f"{column} contains no valid numeric values.")

        df[column] = df[column].fillna(column_mean)

    # Rows without a diet or recipe cannot be grouped or reported.
    rows_before_cleaning = len(df)
    df = df.dropna(subset=["Diet_type", "Recipe_name"]).copy()
    rows_removed = rows_before_cleaning - len(df)

    # Prevent division by zero in ratio calculations.
    carbs_for_ratio = df["Carbs_g"].where(df["Carbs_g"] != 0)
    fat_for_ratio = df["Fat_g"].where(df["Fat_g"] != 0)

    df["Protein_to_Carbs_ratio"] = df["Protein_g"] / carbs_for_ratio
    df["Carbs_to_Fat_ratio"] = df["Carbs_g"] / fat_for_ratio

    print("\nRows removed:", rows_removed)
    print("Rows after cleaning:", len(df))

    print("\nMissing values after cleaning:")
    print(df[numeric_columns + text_columns].isna().sum())

    # Calculate average macronutrients by diet type.
    average_macros = (
        df.groupby("Diet_type")[["Protein_g", "Carbs_g", "Fat_g"]]
        .mean()
        .sort_values("Protein_g", ascending=False)
        .round(2)
    )

    print("\nAverage macronutrients by diet type:")
    print(average_macros)

    average_macros.to_csv(
        OUTPUT_DIR / "average_macronutrients_by_diet.csv"
    )

    # Find the top five protein-rich recipes for each diet type.
    top_protein = (
        df.sort_values(
            ["Diet_type", "Protein_g"],
            ascending=[True, False],
        )
        .groupby("Diet_type", sort=False)
        .head(5)
    )

    top_protein_columns = [
        "Diet_type",
        "Recipe_name",
        "Cuisine_type",
        "Protein_g",
        "Carbs_g",
        "Fat_g",
        "Protein_to_Carbs_ratio",
        "Carbs_to_Fat_ratio",
    ]

    print("\nTop five protein-rich recipes by diet type:")
    print(top_protein[top_protein_columns].to_string(index=False))

    top_protein[top_protein_columns].to_csv(
        OUTPUT_DIR / "top_5_protein_recipes_by_diet.csv",
        index=False,
    )

    # Find the diet type with the highest average protein.
    highest_protein_diet = average_macros["Protein_g"].idxmax()
    highest_protein_value = average_macros.loc[
        highest_protein_diet,
        "Protein_g",
    ]

    print(
        "\nDiet type with the highest average protein: "
        f"{highest_protein_diet} "
        f"({highest_protein_value:.2f} g)"
    )

    pd.DataFrame(
        [
            {
                "Diet_type": highest_protein_diet,
                "Average_Protein_g": highest_protein_value,
            }
        ]
    ).to_csv(
        OUTPUT_DIR / "highest_average_protein_diet.csv",
        index=False,
    )

    # Find the most common cuisine for each diet type.
    cuisine_data = df.dropna(subset=["Cuisine_type"])

    common_cuisines = (
        cuisine_data.groupby("Diet_type")["Cuisine_type"]
        .agg(
            lambda values: (
                values.mode().iloc[0]
                if not values.mode().empty
                else "Unknown"
            )
        )
        .rename("Most_common_cuisine")
    )

    cuisine_counts = (
        cuisine_data.groupby(["Diet_type", "Cuisine_type"])
        .size()
        .rename("Recipe_count")
        .reset_index()
        .sort_values(
            ["Diet_type", "Recipe_count"],
            ascending=[True, False],
        )
    )

    print("\nMost common cuisine by diet type:")
    print(common_cuisines)

    common_cuisines.to_csv(
        OUTPUT_DIR / "most_common_cuisine_by_diet.csv"
    )

    cuisine_counts.to_csv(
        OUTPUT_DIR / "cuisine_counts_by_diet.csv",
        index=False,
    )

    # Save cleaned data and calculated ratios.
    df.to_csv(
        OUTPUT_DIR / "cleaned_diets_with_ratios.csv",
        index=False,
    )

    # Create a bar chart of average macronutrients.
    average_macros.plot(
        kind="bar",
        figsize=(12, 7),
        color=["#4C78A8", "#F58518", "#54A24B"],
    )

    plt.title("Average Macronutrient Content by Diet Type")
    plt.xlabel("Diet type")
    plt.ylabel("Average amount per recipe (g)")
    plt.xticks(rotation=45, ha="right")
    plt.legend(["Protein", "Carbs", "Fat"])
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "average_macronutrients_bar_chart.png",
        dpi=200,
    )
    plt.close()

    # Create a heatmap of average macronutrients.
    plt.figure(figsize=(10, 7))

    sns.heatmap(
        average_macros,
        annot=True,
        fmt=".1f",
        cmap="YlGnBu",
        linewidths=0.5,
    )

    plt.title("Average Macronutrients Heatmap")
    plt.xlabel("Macronutrient")
    plt.ylabel("Diet type")
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "macronutrients_heatmap.png",
        dpi=200,
    )
    plt.close()

    # Create a scatter plot of the top protein-rich recipes.
    scatter_data = top_protein.dropna(
        subset=["Cuisine_type", "Carbs_g", "Protein_g"]
    )

    plt.figure(figsize=(14, 8))

    sns.scatterplot(
        data=scatter_data,
        x="Carbs_g",
        y="Protein_g",
        hue="Cuisine_type",
        style="Diet_type",
        s=130,
    )

    plt.title("Top Five Protein-Rich Recipes by Cuisine")
    plt.xlabel("Carbohydrates (g)")
    plt.ylabel("Protein (g)")
    plt.legend(
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
    )
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "top_protein_recipes_scatter_plot.png",
        dpi=200,
    )
    plt.close()

    print("\nAnalysis complete.")
    print(f"Results saved in: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()