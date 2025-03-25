import os
import dropbox
from dropbox.exceptions import ApiError

# Load securely from environment variables
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# Validation
if not all([DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN]):
    raise ValueError("Missing Dropbox credentials! Set DROPBOX_APP_KEY, DROPBOX_APP_SECRET, and DROPBOX_REFRESH_TOKEN.")

# Create Dropbox client with auto-refresh
dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

def upload_file(file, filename, folder="assignments"):
    dropbox_path = f"/AchievED-LMS/{folder}/{filename}"

    try:
        # Upload the file
        dbx.files_upload(file.read(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))

        # Try to find existing shared link
        shared_link = None
        try:
            existing_links = dbx.sharing_list_shared_links(path=dropbox_path).links
            if existing_links:
                shared_link = existing_links[0]
        except ApiError as e:
            print(f"Warning: Could not list shared links - {e}")

        # Create if missing
        if not shared_link:
            shared_link = dbx.sharing_create_shared_link_with_settings(dropbox_path)

        public_url = shared_link.url.replace("?dl=0", "?raw=1")
        return public_url, dropbox_path

    except ApiError as e:
        print(f"Dropbox API Error: {e}")
        return None, None


def get_file_link(filename, folder="assignments"):
    dropbox_path = f"/AchievED-LMS/{folder}/{filename}"
    try:
        shared_link = dbx.files_get_temporary_link(dropbox_path)
        return shared_link.link
    except ApiError as e:
        print(f"Dropbox API Error: {e}")
        return None


def get_temporary_download_link(path):
    dropbox_path = f"/AchievED-LMS/{path}"
    try:
        shared_link = dbx.files_get_temporary_link(dropbox_path)
        return shared_link.link
    except ApiError as e:
        print(f"Dropbox API Error: {e}")
        return None


def delete_file_from_dropbox(dropbox_path):
    try:
        if not dropbox_path.startswith("/AchievED-LMS/"):
            print(f"Invalid Dropbox path: {dropbox_path}")
            return False

        dbx.files_delete_v2(dropbox_path)
        print(f"File deleted from Dropbox: {dropbox_path}")
        return True

    except ApiError as e:
        print(f"Dropbox API Error: {e}")
        return False
