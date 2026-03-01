import requests
import datetime
from bs4 import BeautifulSoup
from .base import DataSource, AssetObject, AssetType


class WebSource(DataSource):
	def fetch_data(self, url):
		try:
			response = requests.get(url, headers=self.headers, timeout=10)
			response.raise_for_status()
			return {"url": url, "html": response.text, "status": response.status_code}
		except Exception as e:
			print(f"  [Web Error] {e}")
			return None

	def standardize_output(self, raw_data):
		try:
			soup = BeautifulSoup(raw_data["html"], "html.parser")
			for noise in soup(["script", "style", "nav", "footer", "header", "aside"]):
				noise.decompose()

			main_content = soup.find('article') or soup.find('main') or soup
			title = soup.title.string if soup.title else "Untitled Webpage"
			clean_text = main_content.get_text(separator="\n", strip=True)

			return [AssetObject(
				content=clean_text[:5000],
				source_url=raw_data["url"],
				asset_type=AssetType.TEXT,
				source_name="Web",
				metadata={"title": title.strip(), "time": datetime.datetime.now().isoformat()}
			)]
		except Exception as e:
			print(f"  [Parsing Error] {e}")
			return []

