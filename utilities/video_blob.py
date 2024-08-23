import datetime
from azure.storage.blob import (BlobServiceClient , BlobSasPermissions, generate_blob_sas)
from urllib.parse import unquote
import os
from dotenv import load_dotenv
load_dotenv()

storage_account_key = os.getenv("STORAGE_ACCOUNT_KEY")
storage_account_name = os.getenv("STORAGE_ACCOUNT_NAME")
connection_string = os.getenv("CONNECTION_STRING")
container_name = os.getenv("CONTAINER_NAME")

def uploadToBlobStorage(file_path,file_name):
   blob_service_client = BlobServiceClient.from_connection_string(connection_string)
   blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
   with open(file_path,"rb") as data:
      blob_client.upload_blob(data)
      print(f"Uploaded {file_name}.")
   url = get_azure_storage_file_url(file_name)
   return url

def get_azure_storage_file_url(filename):
    print(f"Started getting the azure storage url for {filename}.")
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container_name, filename)
    fileURL = unquote(blob_client.url,encoding = 'utf-8')
    print(f"The azure file storage URL for {filename} is {fileURL}.")
    sas_token = generate_blob_sas(
    account_name=storage_account_name,
    account_key=storage_account_key,
    container_name=container_name,
    blob_name=filename,
    permission=BlobSasPermissions(read=True),
    expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Set SAS token expiry
    )
    print(fileURL + sas_token)
    return fileURL +"?"+ sas_token

# calling a function to perform upload
# uploadToBlobStorage('resources/video.mp4','video.mp4')
