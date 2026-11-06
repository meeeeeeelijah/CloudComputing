import csv
import io
import json
import os
import time
from datetime import datetime, timezone

import azure.functions as func
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp()

REQUIRED_SETTINGS = ("BLOB_CONNECTION_STRING", "BLOB_CONTAINER", "BLOB_NAME")


def json_response(body, status_code=200):
    return func.HttpResponse(
        json.dumps(body, indent=4),
        status_code=status_code,
        mimetype="application/json"
    )


@app.route(
    route="process-diet-data",
    methods=["GET", "POST"],
    auth_level=func.AuthLevel.ANONYMOUS
)
def process_diet_data(req: func.HttpRequest) -> func.HttpResponse:
    start = time.perf_counter()

    missing = [name for name in REQUIRED_SETTINGS if not os.environ.get(name)]
    if missing:
        return json_response(
            {"error": f"Missing app settings: {', '.join(missing)}"},
            500
        )

    try:
        connection_string = os.environ["BLOB_CONNECTION_STRING"]
        container_name = os.environ["BLOB_CONTAINER"]
        blob_name = os.environ["BLOB_NAME"]
        results_blob_name = os.environ.get(
            "RESULTS_BLOB_NAME", "results/diet_results.json"
        )

        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )
        container_client = blob_service_client.get_container_client(
            container_name
        )

        # Download the dataset from Azure Blob Storage
        csv_data = (
            container_client.get_blob_client(blob_name)
            .download_blob()
            .readall()
            .decode("utf-8-sig")
        )

        diet_data = {}
        skipped_rows = 0

        for row in csv.DictReader(io.StringIO(csv_data)):
            try:
                diet_type = row["Diet_type"].strip().lower()
                protein = float(row["Protein(g)"])
                carbs = float(row["Carbs(g)"])
                fat = float(row["Fat(g)"])
            except (KeyError, TypeError, ValueError, AttributeError):
                skipped_rows += 1
                continue

            if not diet_type:
                skipped_rows += 1
                continue

            values = diet_data.setdefault(
                diet_type, {"protein": [], "carbs": [], "fat": []}
            )
            values["protein"].append(protein)
            values["carbs"].append(carbs)
            values["fat"].append(fat)

        results = {}

        for diet_type, values in diet_data.items():
            count = len(values["protein"])
            results[diet_type] = {
                "average_protein_g": round(sum(values["protein"]) / count, 2),
                "average_carbs_g": round(sum(values["carbs"]) / count, 2),
                "average_fat_g": round(sum(values["fat"]) / count, 2),
                "recipe_count": count
            }

        # Save results back to Blob Storage (replaces the Phase 1 local JSON file)
        results_saved = True
        try:
            container_client.get_blob_client(results_blob_name).upload_blob(
                json.dumps(results, indent=4),
                overwrite=True
            )
        except Exception:
            results_saved = False

        metadata = {
            "execution_time_ms": round((time.perf_counter() - start) * 1000, 2),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_blob": f"{container_name}/{blob_name}",
            "results_blob": f"{container_name}/{results_blob_name}" if results_saved else None,
            "diet_count": len(results),
            "total_recipes": sum(item["recipe_count"] for item in results.values()),
            "skipped_rows": skipped_rows
        }

        return json_response({"results": results, "metadata": metadata})

    except Exception as e:
        return json_response({"error": str(e)}, 500)
