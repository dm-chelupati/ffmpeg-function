import os
import shutil
import logging
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_ffmpeg_from_blob(storage_account_name, container_name, blob_name, local_path):
    # Create a credential object
    credential = DefaultAzureCredential()
    
    # Create a BlobServiceClient object
    blob_service_client = BlobServiceClient(
        account_url=f"https://{storage_account_name}.blob.core.windows.net/",
        credential=credential
    )
    # Get a blob client
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    
    # Download the blob to a local file
    with open(local_path, "wb") as file_handle:
        download_stream = blob_client.download_blob()
        file_handle.write(download_stream.readall())

def initialize_ffmpeg():
    storage_account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    container_name = 'azurefiles'
    blob_name = 'ffmpeg'
    local_ffmpeg_path = '/tmp/ffmpeg'
  
   # Check if ffmpeg is already downloaded
    if not os.path.exists(local_ffmpeg_path):
        # Check if running locally
        funcenv = os.getenv('IS_RUNNING_LOCALLY')
        logging.info(f"IS_RUNNING_LOCALLY: {funcenv}")
        if  funcenv:
            print("The environment variable IS_RUNNING_LOCALLY is set and has a value.")
            source_ffmpeg_path = os.path.join(os.getcwd(), 'macffmpeg', 'ffmpeg')
            shutil.copy2(source_ffmpeg_path, local_ffmpeg_path)
            logging.info(f"Running locally, using FFmpeg from macffmpeg folder: {local_ffmpeg_path}")
        else:
            logging.info("FFmpeg not found and not running locally, downloading from Azure Blob")
            # Download the FFmpeg binary from Azure blob
            try:
                download_ffmpeg_from_blob(storage_account_name, container_name, blob_name, local_ffmpeg_path)
                logging.info("ffmpeg downloaded and permissions set")
            except Exception as e:
                logging.error(f"Error downloading FFmpeg binary from Azure File Share: {str(e)}")
    else:
        logging.info("ffmpeg already exists, skipping download and permission modification")

     # Ensure the file is executable
    try:
        os.chmod(local_ffmpeg_path, 0o755)
    except Exception as e:
        logging.error(f"Error setting executable permissions for FFmpeg binary: {str(e)}")

    # Verify the file exists and is not empty
    if os.path.exists(local_ffmpeg_path) and os.path.getsize(local_ffmpeg_path) > 0:
        logging.info(f"ffmpeg is present and has size: {os.path.getsize(local_ffmpeg_path)} bytes")
    else:
        logging.error("ffmpeg download failed or file is empty")

    # Verify permissions
    st = os.stat(local_ffmpeg_path)
    logging.info(f"ffmpeg permissions: {oct(st.st_mode)}")