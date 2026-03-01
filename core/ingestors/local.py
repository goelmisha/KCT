import re
import os
from .base import DataSource, AssetObject, AssetType


class LocalSource(DataSource):
	def fetch_data(self, file_path):
		if not os.path.exists(file_path):
			print(f"  [Local Error] File not found: {file_path}")
			return None
        
		try:
			with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
				return {
					"path": file_path,
					"raw_text": f.read(),
					"ext": os.path.splitext(file_path)[1]
				}
		except Exception as e:
			print(f"  [Local Error] {e}")
			return None

	def _sanitize_pii(self, text):
		return re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', "[REDACTED_EMAIL]", text)

	def standardize_output(self, raw_data):
		clean_content = self._sanitize_pii(raw_data["raw_text"])
		return [AssetObject(
			content=clean_content,
			source_url=f"file://{os.path.abspath(raw_data['path'])}",
			asset_type=AssetType.TEXT,
			source_name="Local",
			metadata={"file_ext": raw_data["ext"], "security": "PII_REDACTED"}
		)]

