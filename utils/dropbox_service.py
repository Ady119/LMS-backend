import os
import dropbox

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

if not DROPBOX_ACCESS_TOKEN:
    raise ValueError("Dropbox API access token is missing! Set DROPBOX_ACCESS_TOKEN in environment variables.")

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def upload_file(file, filename, folder="assignments"):
    dropbox_path = f"/AchievED-LMS/{folder}/{filename}" 

    try:
        # Upload file to Dropbox
        dbx.files_upload(file.read(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))

        shared_link = None
        try:
            existing_links = dbx.sharing_list_shared_links(path=dropbox_path).links
            if existing_links:
                shared_link = existing_links[0] 
        except dropbox.exceptions.ApiError as e:
            print(f"Warning: Unable to list shared links - {e}")

        if not shared_link:
            shared_link = dbx.sharing_create_shared_link_with_settings(dropbox_path)

        public_url = shared_link.url.replace("?dl=0", "?raw=1")

        return public_url, dropbox_path

    except dropbox.exceptions.ApiError as e:
        print(f"Dropbox API Error: {e}")
        return None, None



def get_file_link(filename, folder="assignments"):
    dropbox_path = f"/AchievED-LMS/{folder}/{filename}"

    try:
        shared_link = dbx.files_get_temporary_link(dropbox_path)
        return shared_link.link

    except dropbox.exceptions.ApiError as e:
        print(f"Dropbox API Error: {e}")
        return None

    except Exception as e:
        print(f" Unexpected Error: {e}")
        return None
def get_temporary_download_link(path):
    dropbox_path = f"/AchievED-LMS/{path}"

    try:
        shared_link = dbx.files_get_temporary_link(dropbox_path)
        return shared_link.link
    except dropbox.exceptions.ApiError as e:
        print(f"Dropbox API Error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return None


def delete_file_from_dropbox(dropbox_path):
    try:
        if not dropbox_path.startswith("/AchievED-LMS/"):
            print(f"Invalid Dropbox path: {dropbox_path}")
            return False

        dbx.files_delete_v2(dropbox_path)
        print(f" File deleted from Dropbox: {dropbox_path}")
        return True

    except dropbox.exceptions.ApiError as e:
        print(f" Dropbox API Error: {e}")
        return False

    except Exception as e:
        print(f" Unexpected Error: {e}")
        return False