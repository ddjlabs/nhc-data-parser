FROM python:3.9.5-buster

#Setup work directory and copy over the requirements.txt and the app folder (including its contents)
WORKDIR /app
COPY requirements.txt /app/
COPY app/. /app/

#These commands properly installs the necessary packages to use SQLAlchemy with MariaDB and the MariaDB Connector for Python3.
#See this URL: https://mariadb.com/resources/blog/using-sqlalchemy-with-mariadb-connector-python-part-1/
RUN apt update && apt install wget curl apt-transport-https htop -y
RUN wget https://downloads.mariadb.com/MariaDB/mariadb_repo_setup
RUN echo "b3d5fb3ea9791e93b64a97e8b8a5faacd6e744e9d2c1c7cc3453f0390aa76569 mariadb_repo_setup" | sha256sum -c -
RUN chmod +x mariadb_repo_setup && ./mariadb_repo_setup --mariadb-server-version="mariadb-10.5"
RUN apt update && apt install libmariadb3 libmariadb-dev -y && rm mariadb_repo_setup

#Run PIP Requirements file. This was based on my virtual env on my workstation
RUN pip install -r requirements.txt

#Clear out any raw-files that may have copied from the source app.
RUN rm -rf app/raw-files/*

#Execute the main app file to start the thread.
CMD [ "python3", "main.py" ]
