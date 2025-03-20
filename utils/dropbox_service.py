import os
import dropbox

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

if not DROPBOX_ACCESS_TOKEN:
    raise ValueError("Dropbox API access token is missing! Set DROPBOX_ACCESS_TOKEN in environment variables.")

# Initialize Dropbox client
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def upload_file(file, filename, folder="assignments"):
    dropbox_path = f"/AchievED-LMS/{folder}/{filename}"  # Store in the specified folder

    try:
        # Upload file
        dbx.files_upload(file.read(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))

        # (public URL)
        shared_link = dbx.sharing_create_shared_link_with_settings(dropbox_path)
        return shared_link.url.replace("?dl=0", "?raw=1")

    except dropbox.exceptions.ApiError as e:
        print(f"Dropbox API Error: {e}")
        return None

def get_file_link(filename, folder="assignments"):
    """Retrieve a Dropbox temporary link for a stored file."""

    dropbox_path = f"/AchievED-LMS/{folder}/{filename}"  # Ensure correct folder

    try:
        shared_link = dbx.files_get_temporary_link(dropbox_path)
        return shared_link.link  # ✅ Dropbox generates a temporary link

    except dropbox.exceptions.ApiError as e:
        print(f"❌ Dropbox API Error: {e}")
        return None  # Return None instead of crashing

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return None  # Catch all unexpected errors


def delete_file_from_dropbox(file_path):
    """Deletes a file from Dropbox using its stored path."""
    try:
        if not file_path.startswith("/AchievED-LMS/"):
            print(f"Invalid Dropbox path: {file_path}")
            return False

        # ✅ Delete file from Dropbox
        dbx.files_delete_v2(file_path)
        print(f"✅ File deleted from Dropbox: {file_path}")
        return True

    except dropbox.exceptions.ApiError as e:
        print(f"❌ Dropbox API Error: {e}")
        return False

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False