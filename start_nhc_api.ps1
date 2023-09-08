clear-host
# Activate the Virtual Environment
Set-Location 'C:\Users\doug\OneDrive\03-dev-projects\nhc_weewx_api\.venv\Scripts'
.\Activate

# Reset the location to the app directory
Set-Location 'C:\Users\doug\OneDrive\03-dev-projects\nhc_weewx_api\app'

#Execute the main program (main.py)
python.exe main.py