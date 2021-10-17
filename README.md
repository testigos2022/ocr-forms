
### scraping E14
* setup
```shell
# chromedriver installation
CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
    wget https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip
sudo unzip chromedriver_linux64.zip -d /usr/bin
sudo chmod +x /usr/bin/chromedriver

# python venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
* scrape E14
```shell
DATA_PATH=colombia_election_forms python scraping_forms/run_e14_scraper.py
```