import json
import tempfile
from pathlib import Path
from typing import Any

import requests


class IpifyClient:
    """Client for the ipify service."""

    API_URL = "https://api.ipify.org"

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout

    def get_ip(self) -> str:
        """Return the current public IP address."""
        response = requests.get(
            self.API_URL,
            params={"format": "json"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        ip_address = response.json().get("ip")
        if not ip_address:
            raise ValueError("Сервис ipify не вернул IP-адрес")
        return str(ip_address)


class IpInfoClient:
    """Client for the IPinfo geolocation service."""

    API_URL = "https://ipinfo.io"

    def __init__(self, token: str | None = None, timeout: int = 10) -> None:
        self.token = token
        self.timeout = timeout

    def get_geo(self, ip_address: str) -> dict[str, Any]:
        """Return geolocation data for an IP address."""
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        response = requests.get(
            f"{self.API_URL}/{ip_address}/geo",
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Сервис IPinfo вернул данные неверного формата")
        return data


class YandexDiskClient:
    """Client for folder creation and file upload to Yandex Disk."""

    API_URL = "https://cloud-api.yandex.net/v1/disk/resources"

    def __init__(self, token: str, timeout: int = 30) -> None:
        self.headers = {"Authorization": f"OAuth {token}"}
        self.timeout = timeout

    def create_folder(self, folder_path: str) -> None:
        """Create a folder unless it already exists."""
        response = requests.put(
            self.API_URL,
            headers=self.headers,
            params={"path": folder_path},
            timeout=self.timeout,
        )
        if response.status_code not in (201, 409):
            response.raise_for_status()

    def upload_file(
            self,
            local_path: Path,
            disk_path: str,
            overwrite: bool = True,
    ) -> None:
        """Request an upload URL and upload a local file."""
        response = requests.get(
            f"{self.API_URL}/upload",
            headers=self.headers,
            params={
                "path": disk_path,
                "overwrite": str(overwrite).lower(),
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        upload_url = response.json().get("href")
        if not upload_url:
            raise ValueError("Яндекс.Диск не вернул ссылку для загрузки")

        with local_path.open("rb") as file:
            upload_response = requests.put(
                upload_url,
                data=file,
                timeout=self.timeout,
            )
        upload_response.raise_for_status()


def save_json(data: dict[str, Any], file_path: Path) -> None:
    """Save a dictionary as readable UTF-8 JSON."""
    with file_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def main() -> None:
    """Run the complete IP detection and upload workflow."""
    yandex_token = input("Введите токен Яндекс.Диска: ").strip()
    if not yandex_token:
        print("Ошибка: токен Яндекс.Диска не введён")
        return

    folder_name = "ip_detector"
    file_name = "ip_info.json"

    ipify = IpifyClient()
    ipinfo = IpInfoClient()
    yandex_disk = YandexDiskClient(token=yandex_token)

    try:
        ip_address = ipify.get_ip()
        geo_data = ipinfo.get_geo(ip_address)

        yandex_disk.create_folder(folder_name)
        with tempfile.TemporaryDirectory() as temp_directory:
            local_path = Path(temp_directory) / file_name
            save_json(geo_data, local_path)
            disk_path = f"{folder_name}/{file_name}"
            yandex_disk.upload_file(local_path, disk_path)

        print(f"Файл успешно загружен на Яндекс.Диск: {disk_path}")
    except (requests.RequestException, ValueError) as error:
        print(f"Ошибка при работе с API: {error}")


if __name__ == "__main__":
    main()
