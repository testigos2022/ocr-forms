
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
pip install -r scraping_forms/requirements.txt
```
* scrape E14
```shell
DATA_PATH=colombia_election_forms python scraping_forms/run_e14_scraper.py
```
#### just one example
![sample](scraping_forms/images/sample.png)
#### scraping does NOT work in headless mode!
![image](scraping_forms/images/screenshot_headless_being_blocked.png)
* TODO: find out how to prevent being detected