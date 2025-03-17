# ClimateTemplate
Project processes climate data by cropping raster files, placing them on a  
template, and transferring them to an SFTP and FTP server for website integration.

## Requirements

Before using the script, please ensure that the following dependencies are installed:

- Python
- Libraries specified in the `requirements.txt` file
- A folder containing the template files with the following directory structure (these folders are **not** included in the GitHub repository). It is crucial to maintain this folder hierarchy and naming conventions. Additionally, the raster templates must follow the naming convention with the following parameters: `bg_(parameter_name)_(depth, if applicable)`. Here are examples of template names used during script development:

    - `bg_AWD_0-40cm`  # Available Water Depth 0-40 cm 
    - `bg_AWR_0-40cm`  # Available Water Reserve 0-40 cm
    - `bg_AWP_0-40cm`  # Available Water Potential 0-40 cm
    - `bg_AWD_0-100cm` # Available Water Depth 0-100 cm
    - `bg_AWR_0-100cm` # Available Water Reserve 0-100 cm
    - `bg_AWP_0-100cm` # Available Water Potential 0-100 cm
    - `bg_AWD_0-200cm` # Available Water Depth 0-200 cm
    - `bg_AWR_0-200cm` # Available Water Reserve 0-200 cm
    - `bg_AWP_0-200cm` # Available Water Potential 0-200 cm
    - `bg_FWI_GenZ`    # Fire Weather Index GenZ
    - `bg_DFM10H`      # Daily Fire Meteorological Index for 10 hours
    - `bg_HI`          # Heat Index
    - `bg_UTCI`        # Universal Thermal Climate Index

The directory structure should look like this:

```
/ (root)
│
├── data/ 
│      ├── raster_templates 
│      │      └── background_templates
│      │              ├── templates_v1
│      │              │      ├── CZ
│      │              │      ├── DE
│      │              │      ├── EN
│      │              │      ├── HR
│      │              │      ├── PL
│      │              │      ├── SI
│      │              │      └── SK
│      │              └── templates_v2
│      │                      ├── CZ
│      │                      ├── DE
│      │                      ├── EN
│      │                      ├── HR
│      │                      ├── PL
│      │                      ├── SI
│      │                      └── SK
```

- Additionally, create a `.env` file in the root directory with the following content:

```
/ (root)
│
├── .env
```

The `.env` file should contain the following environment variables:

```
SFTP_HOST=your_host
SFTP_USERNAME=your_username
SFTP_PASSWORD=your_password
SFTP_PORT=22
FTP_HOST=your_host
FTP_USERNAME=your_username
FTP_PASSWORD=your_password
```

- The script is configured to work with data available at `//monospace/mendelu/`. Please ensure that you have access to this resource before using the script. Additionally, note that the data used by the script (as of today) may not yet be available on this resource.
```
