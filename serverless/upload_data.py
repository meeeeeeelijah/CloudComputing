from azure.storage.blob import BlobServiceClient

CONNECTION_STRING = (
    "DefaultEndpointsProtocol=http;"
    "AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
)

CONTAINER_NAME = "diet-data"
BLOB_NAME = "All_Diets.csv"
CSV_FILE = "data/All_Diets.csv"


def main():
    blob_service_client = BlobServiceClient.from_connection_string(
        CONNECTION_STRING
    )

    container_client = blob_service_client.get_container_client(
        CONTAINER_NAME
    )

    try:
        container_client.create_container()
        print(f"Created container: {CONTAINER_NAME}")
    except Exception:
        print(f"Container already exists: {CONTAINER_NAME}")

    blob_client = container_client.get_blob_client(BLOB_NAME)

    with open(CSV_FILE, "rb") as data:
        blob_client.upload_blob(
            data,
            overwrite=True
        )

    print(
        f"Uploaded {CSV_FILE} "
        f"to {CONTAINER_NAME}/{BLOB_NAME}"
    )


if __name__ == "__main__":
    main()
