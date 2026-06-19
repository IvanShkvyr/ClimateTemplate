"""LEGACY"""

from ftplib import FTP, error_perm, all_errors
import os


def connect_to_ftp(host: str, username: str, password: str) -> FTP:
    """
    Establishes a connection to an FTP server using the provided credentials.

    This function attempts to connect to the specified FTP server using the 
    given username and password. If the connection is successful, it returns 
    the FTP object; otherwise, it prints an error message and returns None.

    Args:
        host (str): The hostname or IP address of the FTP server.
        username (str): The username for authentication.
        password (str): The password for authentication.

    Returns:
        FTP: An FTP connection object if successful; otherwise, None.
    """
    try:
        ftp = FTP(host)
        ftp.login(user=username, passwd=password)
        print(f"Successfully connected to FTP server: {host}")
        return ftp
    except Exception as e:
        print(f"FTP connection error: {e}")
        return None


def upload_files_to_ftp(
        ftp_connection: FTP, 
        local_folder: str, 
        remote_folder: str
    ) -> list[str]:
    """
    Uploads all files from a local folder to a remote directory on the server.

    This function attempts to navigate to the specified remote folder. If the
    folder does not exist, it is created. Then, all files from the local folder
    are uploaded to the remote directory.

    Args:
        ftp (FTP): The FTP connection object.
        local_folder (str): The local directory containing files to be uploaded.
        remote_folder (str): The target directory on the FTP server.

    Returns:
        list[str]: A list of successfully uploaded filenames.
    """
    uploaded_files = []

    try:
        # Attempt to change to the target directory
        ftp_connection.cwd(remote_folder)
        print(f"Changed directory to {remote_folder}")
    except error_perm:
        try:
            # Create the directory if it does not exist
            ftp_connection.mkd(remote_folder)
            ftp_connection.cwd(remote_folder)
            print(f"Created and changed to directory {remote_folder}")
        except Exception as e:
            print(f"Failed to create directory {remote_folder}: {e}")
            return uploaded_files

    # Iterate through files in the local directory and upload them
    for filename in os.listdir(local_folder):
        local_path = os.path.join(local_folder, filename)

        if os.path.isfile(local_path):
            try:
                with open(local_path, 'rb') as file:
                    ftp_connection.storbinary(f'STOR {filename}', file)
                uploaded_files.append(filename)
                print(f"Uploaded {filename} → {remote_folder}")
            except Exception as e:
                print(f"Upload failed for {filename}: {e}")

    return uploaded_files


def disconnect_from_ftp(ftp_connection: FTP) -> None:
    """
    Safely disconnects from the FTP server.

    This function attempts to properly close an active FTP connection. If the 
    connection is already closed or does not exist, it prints an appropriate 
    message. In case of an error during disconnection, it tries to forcefully 
    close the connection.

    Args:
        ftp_connection (FTP): The active FTP connection object or None.

    Returns:
        None: This function does not return a value but prints status messages.
    """
    try:
        # Check if the connection exists
        if ftp_connection is None:
            print("FTP connection is already closed or does not exist.")
            return
        
        # Properly close the FTP connection
        ftp_connection.quit()
        print("Successfully disconnected from the FTP server.")
    
    except all_errors as e:
        print(f"Error while disconnecting from FTP: {e}")
        
        try:
            # Forcefully close the connection if an error occurs
            ftp_connection.close()
            print("Forced closure of FTP connection.")
        except Exception:
            pass


