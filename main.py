import os
import json
import requests


class IpifyClient:
    """Класс для работы с сервисом ipify для получения текущего IP."""

    URL = "https://ipify.org"

    def get_current_ip(self) -> str:
        """Получает текущий публичный IP-адрес."""
        response = requests.get(self.URL)
        response.raise_for_status()
        return response.json().get("ip")


class IpInfoClient:
    """Класс для работы с сервисом ipinfo для геодетекции по IP."""

    BASE_URL = "https://ipinfo.io/{}/geo"

    def get_geo_info(self, ip_address: str) -> dict:
        """Получает географическую информацию по указанному IP."""
        url = self.BASE_URL.format(ip_address)
        response = requests.get(url)
        response.raise_for_status()
        return response.json()


class YandexDiskUploader:
    """Класс для работы с Яндекс.Диском через REST API."""

    BASE_URL = "https://yandex.net"

    def __init__(self, token: str):
        self.headers = {
            "Authorization": f"OAuth {token}",
            "Content-Type": "application/json"
        }

    def create_folder(self, folder_path: str) -> bool:
        """Создает папку на Яндекс.Диске. Возвращает True в случае успеха."""
        url = f"{self.BASE_URL}resources"
        params = {"path": folder_path}
        response = requests.put(url, headers=self.headers, params=params)

        # Заменили "in" на прямое сравнение, чтобы избежать ошибок форматирования
        if response.status_code == 201 or response.status_code == 409:
            return True
        response.raise_for_status()
        return False

    def upload_file_from_memory(self, folder_path: str, filename: str, data: dict):
        """Загружает JSON-данные из памяти напрямую на Яндекс.Диск без сохранения на диск."""
        # 1. Получаем URL для загрузки
        upload_url_endpoint = f"{self.BASE_URL}resources/upload"
        full_path = f"{folder_path}/{filename}"
        params = {"path": full_path, "overwrite": "true"}

        response = requests.get(upload_url_endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        upload_url = response.json().get("href")

        # Превращаем словарь в строку JSON в кодировке bytes
        json_bytes = json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8')

        # 2. Отправляем байты данных по полученному URL
        upload_response = requests.put(upload_url, data=json_bytes)
        upload_response.raise_for_status()


def main():
    # Токен запрашивается у пользователя (или берется из переменных окружения),
    # чтобы не коммитить его в публичный репозиторий GitHub
    token = os.getenv("YANDEX_DISK_TOKEN") or input("Введите ваш Яндекс.Диск токен: ").strip()

    if not token:
        print("Ошибка: Токен Яндекс.Диска не может быть пустым.")
        return

    folder_name = "IP_Geolocations"
    file_name = "geo_info.json"

    try:
        # Инициализация клиентов
        ipify = IpifyClient()
        ipinfo = IpInfoClient()
        uploader = YandexDiskUploader(token)

        # Шаг 1: Получаем свой IP
        print("Получение текущего IP-адреса...")
        current_ip = ipify.get_current_ip()
        print(f"Ваш IP: {current_ip}")

        # Шаг 2: Получаем гео-данные по IP
        print("Запрос географической информации...")
        geo_data = ipinfo.get_geo_info(current_ip)

        # Шаг 3: Создаем папку на Яндекс.Диске
        print(f"Создание папки '{folder_name}' на Яндекс.Диске...")
        uploader.create_folder(folder_name)

        # Шаг 4: Загружаем данные (без создания промежуточных локальных файлов)
        print(f"Загрузка файла {file_name} на Яндекс.Диск...")
        uploader.upload_file_from_memory(folder_name, file_name, geo_data)

        print(f"Успех! Файл '{folder_name}/{file_name}' успешно сохранен на вашем Яндекс.Диске.")

    except requests.exceptions.HTTPError as http_err:
        print( f"Произошла ошибка HTTP: {http_err}")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")


if __name__ == "__main__":
    main()
