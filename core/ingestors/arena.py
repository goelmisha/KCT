import requests
from .base import DataSource, AssetObject, AssetType


class ArenaSource(DataSource):
	def fetch_data(self, channel_slug):
		url = f"https://api.are.na/v3/channels/{channel_slug}/contents"
		try:
			response = requests.get(url, params={"per": 20}, headers=self.headers, timeout=10)
			response.raise_for_status()
			return response.json()
		except Exception as e:
			print(f"  [Arena Error] {e}")
			return None

	def standardize_output(self, raw_data):
		assets = []
		items = raw_data.get("data") or raw_data.get("contents") or []

		for block in items:
			b_type = block.get("class") or block.get("type")
			try:
				content, a_type = self._parse_block(block, b_type)
				if content:
					assets.append(AssetObject(
						content=content,
						source_url=f"https://www.are.na/block/{block.get('id')}" if b_type != "Channel" else content,
						asset_type=a_type,
						source_name="Arena",
						metadata={"id": block.get("id"), "raw_type": b_type}
					))
			except Exception:
				continue
		return assets

	def _parse_block(self, block, b_type):
		if b_type == "Image":
			img = block.get("image", {})
			url = img.get("src") or img.get("large") or img.get("display", {}).get("url")
			return url, AssetType.IMAGE

		if b_type == "Text":
			c = block.get("content")
			text = c.get("plain") if isinstance(c, dict) else c
			return text, AssetType.TEXT

		if b_type == "Attachment":
			return block.get("attachment", {}).get("url"), AssetType.DOCUMENT

		if b_type in ["Link", "Channel"]:
			url = block.get("source", {}).get("url") if b_type == "Link" else f"https://www.are.na/channel/{block.get('slug')}"
			return url, AssetType.LINK

		return None, None
