import csv
import io
import json
import os

import azure.functions as func
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp()


@app.route(
    route="process-diet-data",
    methods=["GET", "POST"],
    auth_level=func.AuthLevel.ANONYMOUS
)
def process_diet_data(req: func.HttpRequest) -> func.HttpResponse:
    try:
        connection_string = os.environ["BLOB_CONNECTION_STRING"]
        container_name = os.environ["BLOB_CONTAINER"]
        blob_name = os.environ["BLOB_NAME"]

        # Connect to Azurite
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )

        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )

        # Download CSV from Azurite
        csv_data = blob_client.download_blob().readall().decode("utf-8")

        # Read CSV
        reader = csv.DictReader(io.StringIO(csv_data))

        # Store nutritional values by diet type
        diet_data = {}

        for row in reader:
            diet_type = row["Diet_type"]

            protein = float(row["Protein(g)"])
            carbs = float(row["Carbs(g)"])
            fat = float(row["Fat(g)"])

            if diet_type not in diet_data:
                diet_data[diet_type] = {
                    "protein": [],
                    "carbs": [],
                    "fat": []
                }

            diet_data[diet_type]["protein"].append(protein)
            diet_data[diet_type]["carbs"].append(carbs)
            diet_data[diet_type]["fat"].append(fat)

        # Calculate averages
        results = {}

        for diet_type, values in diet_data.items():
            results[diet_type] = {
                "average_protein_g": round(
                    sum(values["protein"]) / len(values["protein"]),
                    2
                ),
                "average_carbs_g": round(
                    sum(values["carbs"]) / len(values["carbs"]),
                    2
                ),
                "average_fat_g": round(
                    sum(values["fat"]) / len(values["fat"]),
                    2
                ),
                "recipe_count": len(values["protein"])
            }

        # Save results as simulated NoSQL database
        project_root = os.path.dirname(os.path.abspath(__file__))

        output_dir = os.path.join(
            project_root,
            "serverless",
            "database"
        )

        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(
            output_dir,
            "diet_results.json"
        )

        with open(output_path, "w") as output_file:
            json.dump(results, output_file, indent=4)

        # Return results
        return func.HttpResponse(
            json.dumps(results, indent=4),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "error": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )
