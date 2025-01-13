import os
import sys
import logging
import subprocess
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
from init_ffmpeg import initialize_ffmpeg
initialize_ffmpeg()

def upload_file_to_blob(storage_account_name, container_name, file_path, blob_name):
    credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(
        account_url=f"https://{storage_account_name}.blob.core.windows.net/",
        credential=credential
    )
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    return blob_client.url

@app.route(route="ffmpeg_trigger")
def main(req: func.HttpRequest) -> func.HttpResponse:
    # Azure File Share connection details
    storage_account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    container_name = 'azurefiles'
    local_ffmpeg_path = '/tmp/ffmpeg'
    logging.info(f"setting local photo variables.")
       # Paths to input photos and output file
    input_photo1 = os.path.join(os.getcwd(), 'photo1.jpg')
    input_photo2 = os.path.join(os.getcwd(), 'photo2.jpg')
    output_photo = '/tmp/output_photo.jpg'
    logging.info(f"finished setting local photo variables.")
    # Check if the output file already exists and delete it
    if os.path.exists(output_photo):
        try:
            os.remove(output_photo)
            logging.info(f"Existing output file {output_photo} deleted.")
        except Exception as e:
            return func.HttpResponse(f"Error deleting existing output file: {str(e)}", status_code=500)

 # Command to resize the images to the same height and merge them side by side using ffmpeg
    # Check if ffmpeg is  downloaded
    if os.path.exists(local_ffmpeg_path):
        command = (
        f"{local_ffmpeg_path} -i {input_photo1} -i {input_photo2} "
        f"-filter_complex '[0:v]scale=-1:1000[scaled1];[1:v]scale=-1:1000[scaled2];[scaled1][scaled2]hstack=inputs=2' "
        f"-frames:v 1 -update 1 {output_photo}"
        )
        logging.info(f"Running FFmpeg command: {command}")
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logging.info(f"FFmpeg stdout: {result.stdout.decode()}")
            logging.error(f"FFmpeg stderr: {result.stderr.decode()}")
            blob_url = upload_file_to_blob(storage_account_name, container_name, output_photo, 'output_photo.jpg')
            return func.HttpResponse(f"Photos merged successfully: {result.stdout.decode()}", status_code=200)
        except subprocess.CalledProcessError as e:
            error_message = f"ffmpeg execution error: {str(e)}, stdout: {e.stdout.decode()}, stderr: {e.stderr.decode()}"
            logging.error(error_message)
            return func.HttpResponse(error_message, status_code=500)
    else:
        logging.info("ffmpeg is not downloaded")
        return func.HttpResponse("ffmpeg is not downloaded", status_code=500)
  