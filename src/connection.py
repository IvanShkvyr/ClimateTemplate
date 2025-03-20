from datetime import datetime
from ftplib import FTP, error_perm, all_errors
from paramiko import SSHException
from pathlib import Path
import os

import pysftp


def connect_to_sftp(
                    host: str,
                    username: str,
                    password: str,
                    port: int
                    ) -> pysftp.Connection:
    """
    Connects to the SFTP server using the provided credentials and port.

    This function attempts to establish a connection to an SFTP server with the
    given host, username, password, and port. It also checks if the 'data'
    directory exists on the server, returning the connection object if
    successful, or None if the connection fails or the directory is not found.

    Args:
        host (str): The hostname or IP address of the SFTP server.
        username (str): The username used to authenticate to the server.
        password (str): The password used to authenticate to the server.
        port (int): The port number to connect to the SFTP server.

    Returns:
        pysftp.Connection: The connection object if successful, or None if the
            connection fails.
    """
    cnopts = pysftp.CnOpts()
    
    # # NOTE: You should use the following block to explicitly load known host keys:
    # #
    # # Example:
    # # cnopts.hostkeys.load(os.path.expanduser('~/.ssh/known_hosts'))
    # #
    # # This will load the host keys from your known_hosts file to verify the server's identity.
    # # It is highly recommended to use host key verification for security purposes.
    
    # Disabling host key checking (not secure, use for testing only)
    cnopts.hostkeys = None
    
    try:
        # Establishing connection using context manager
        sftp = pysftp.Connection(
                                host=host,
                                username=username,
                                password=password,
                                port=port,
                                cnopts=cnopts
                                )
        print(f"Connected successfully to SFTP server on host {host}")
            
        # Checking if 'data' directory exists on the server
        try:
            files = sftp.listdir("data")
            print(f"Files in 'data' directory: {files}")
            # Returning the connection object
            return sftp

        except FileNotFoundError:
            print("Directory 'data' not found on the server.")
            return None

    except SSHException as e:
        print(f"Error connecting to SFTP server: {e}")
        return None

    except Exception as e:
        # Catching general exceptions for better diagnostics
        print(f"An unexpected error occurred: {e}")
        return None


def upload_directory_in_sftp(
        sftp: pysftp.Connection,
        source: str,
        destination: str
) -> None:
    """
    Recursively uploads a local directory structure to an SFTP server.

    This function iterates through all files and subdirectories within the
    specified local source directory and uploads them to the given remote
    destination on the SFTP server. If a directory does not exist on the server,
    it is created. Files are then uploaded while handling potential errors.

    Args:
        sftp (pysftp.Connection): The SFTP connection object.
        source (str): The path to the local directory to be uploaded.
        destination (str): The path to the target directory on the remote SFTP
            server.

    Returns:
        None
    """
    source = Path(source)
    destination = Path(destination)

    # Check the SFTP connection
    if sftp is None:
        print("Not connected to SFTP server")
        return

    # Recursively iterate through all subdirectories and files
    for local_path in source.rglob("*"):
        # Get the relative path (excluding the base folder)
        relative_path = local_path.relative_to(source)

        # Construct the remote path
        remote_path = destination / relative_path
        remote_path_str = str(remote_path).replace(os.sep, "/")

        if local_path.is_dir():
            # Create the corresponding directory on the server
            try:
                sftp.makedirs(remote_path_str)
                print(f"Directory created: {remote_path_str}")
            except OSError:
                print(f"Directory already exists: {remote_path_str}")
            except Exception as err:
                print(f"Failed to create directory {remote_path_str}: {err}")
        else:
            # Upload the file
            try:
                sftp.put(str(local_path), remote_path_str)
                print(f"Uploaded: {local_path} → {remote_path_str}")
            except SSHException as e:
                print(f"SSH error while uploading {local_path}: {e}")
            except Exception as e:
                print(f"Failed to upload {local_path}: {e}")


def remove_old_sftp_folders(sftp_client: pysftp.Connection, 
                            remote_root: str, 
                            days_threshold: int = 7
                            ) -> None:
    """
    Removes directories in the specified remote root on the SFTP server that are
    older than a specified number of days.

    This function checks the directories in the given remote root path and
    deletes those whose names are formatted as dates and exceed the specified
    age threshold. The directories are identified by their names, which are
    expected to be in the 'YYYY-MM-DD' format. If the directory is older than 
    the specified threshold (in days), it will be removed.

    Args:
        sftp_client (pysftp.Connection): The SFTP connection object used to
            interact with the server.
        remote_root (str): The path to the remote directory on the SFTP server
            where directories will be checked.
        days_threshold (int, optional): The number of days a directory must be
            older than to be removed. Default is 7.

    Returns:
        None: This function does not return any value.
    """
    current_time = datetime.now()

    try:
        # Fetching the list of directories in the remote root
        dir_entries = sftp_client.listdir_attr(remote_root)
        
        for entry in dir_entries:
            try:
                # Attempting to parse directory name as a date
                dir_date = datetime.datetime.strptime(
                                                    entry.filename, "%Y-%m-%d"
                                                    )
                # Checking if the directory is older than the threshold
                if (current_time - dir_date).days > days_threshold:
                    _remove_directory_in_sftp(
                                            sftp_client,
                                            remote_root,
                                            entry.filename
                                            )
            except ValueError:
                # Skipping directories whose names are not valid date formats
                continue
    except Exception as e:
        print(f"Error while working with the directory {remote_root}: {e}")


def _remove_directory_in_sftp(
    sftp_client: pysftp.Connection, 
    remote_root: str, 
    dir_name: str
) -> None:
    """
    Recursively deletes a directory and its contents from the remote SFTP server

    This function takes a remote directory specified by `remote_root` and
    `dir_name`, checks if it exists, and then recursively deletes all files and
    subdirectories within it before deleting the directory itself.

    Args:
        sftp_client (pysftp.Connection): The active SFTP connection object used
            to interact with the server.
        remote_root (str): The root directory on the remote SFTP server where
            the target directory is located.
        dir_name (str): The name of the directory to be deleted.

    Returns:
        None: This function does not return any value.
    """
    # Construct the full remote path
    remote_path = f"{remote_root}/{dir_name}".replace('\\', '/')
    
    try:
        # Check if the directory exists
        if not sftp_client.exists(remote_path):
            print(f"Directory {remote_path} does not exist.")
            return
            
        # Recursively delete files and subdirectories
        for entry in sftp_client.listdir_attr(remote_path):
            entry_name = entry.filename
            full_remote_path = f"{remote_path}/{entry_name}".replace('\\', '/')
            
            if sftp_client.isdir(full_remote_path):
                # Recursively delete subdirectories
                _remove_directory_in_sftp(
                    sftp_client, 
                    remote_path,
                    entry_name
                )
            else:
                # Delete file
                sftp_client.remove(full_remote_path)
                print(f"Deleted file: {full_remote_path}")
        # Remove the empty directory
        sftp_client.rmdir(remote_path)
        print(f"Deleted directory: {remote_path}")
    
    except Exception as e:
        print(f"Error occurred while deleting directory {remote_path}: {e}")


def disconnect_from_sftp(sftp: pysftp.Connection) -> None:
    """
    Disconnects from the SFTP server and closes the connection.

    This function checks if the SFTP connection is active. If it is, it attempts
    to close the connection. If the connection is already closed or was never
    established, it prints a corresponding message.

    Args:
        sftp (pysftp.Connection): The SFTP connection object to be closed.
            If None, the function will print a message indicating that no
            connection was made.

    Returns:
        None
    """
    if sftp is not None:
        try:
            # Close the connection
            sftp.close() 
            print("Successfully disconnected from SFTP server.")
        except Exception as e:
            print(f"Failed to disconnect from SFTP server: {e}")
    else:
        print("No SFTP server was connected.")


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
    Uploads all files from a local folder to a remote directory on the FTP server.

    This function attempts to navigate to the specified remote folder. If the folder 
    does not exist, it is created. Then, all files from the local folder are uploaded 
    to the remote directory.

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

