# Socket Pyscrapy
Low level sockets implementation of a python webscraper.

## Note
Do not confuse this project with the [Scrapy](https://scrapy.org/) project. This is a low level socket implementation and not the abstracted library.

## Installation

1. Install [Python 3.7.4 (>=3.4)](https://www.python.org/downloads/release/python-374/) in your system
2. Clone this repository
3. Run the following commands in this repository's directory on your local machine:
    ```bash
    pip install -r requirements.txt
    ```
4. Set up a firebase project to store the results of the scraper [here](https://console.firebase.google.com).
    1. **Set up realtime database**. Go to `Database` on the left panel, then scroll down and look for realtime database. You want this as opposed to Cloud Firestore. We don't need region replication redundancy or any cool features.
    2. **Generate Private Key**. Go to `Project Settings` > `Service accounts` > `Generate new private key`
    3. Download generated private key
    4. Set your OS environment variables:
        * `GOOGLE_APPLICATION_CREDENTIALS` to the absolute path of where you downloaded the private key
        * `FIREBASE_DATABASE_URL` to the url of your firebase realtime database you set up in 1.

## To View Populated Database

Visit [https://asia-east2-socket-pyscrapy.cloudfunctions.net/data](https://asia-east2-socket-pyscrapy.cloudfunctions.net/data) to get **ALL** of the scraper's visited sites.
Visit [https://asia-east2-socket-pyscrapy.cloudfunctions.net/data/5](https://asia-east2-socket-pyscrapy.cloudfunctions.net/data/5) to show only the first `5` results. Change `5` to anything you like. 
