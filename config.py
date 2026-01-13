from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Список администраторов
ADMINS = [859416796]

# Для обратной совместимости
PHOTO_ADMIN_ID = ADMIN_ID

# Список фотографов
PHOTOGRAPHERS = {
    "anna": {
        "name": "Анна Портретная", 
        "photos": [
            "static/photos/anna1.jpg",
            "static/photos/anna2.jpg",
            "static/photos/anna3.jpg"
        ]
    },
    "ivan": {
        "name": "Иван Семейный",
        "photos": [
            "static/photos/ivan1.jpg",
            "static/photos/ivan2.jpg",
            "static/photos/ivan3.jpg"
        ]
    },
    "maria": {
        "name": "Мария Свадебная",
        "photos": [
            "static/photos/maria1.jpg",
            "static/photos/maria2.jpg",
            "static/photos/maria3.jpg"
        ]
    }
}
