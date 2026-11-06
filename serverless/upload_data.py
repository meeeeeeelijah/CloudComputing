import os
import sys

from azure.storage.blob import BlobServiceClient

# Azure: set AZURE_STORAGE_CONNECTION_STRING to the storage account connection string.
# Local: falls back to Azurite.
AZURITE_CONNECTION_STRING = (
    "DefaultEndpointsProtocol=http;"
    "AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
)

CONNECTION_STRING = os.environ.get(
    "AZURE_STORAGE_CONNECTION_STRING", AZURITE_CONNECTION_STRING
)
CONTAINER_NAME = os.environ.get("BLOB_CONTAINER", "diet-data")
BLOB_NAME = os.environ.get("BLOB_NAME", "All_Diets.csv")
CSV_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "All_Diets.csv"
)


def main():
    target = "Azurite" if CONNECTION_STRING == AZURITE_CONNECTION_STRING else "Azure"
    blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)

    if not container_client.exists():
        container_client.create_container()
        print(f"Created container: {CONTAINER_NAME}")
    else:
        print(f"Container already exists: {CONTAINER_NAME}")

    with open(CSV_FILE, "rb") as data:
        container_client.get_blob_client(BLOB_NAME).upload_blob(data, overwrite=True)

    print(f"Uploaded {CSV_FILE} to {target}: {CONTAINER_NAME}/{BLOB_NAME}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Upload failed: {e}")
        sys.exit(1)
