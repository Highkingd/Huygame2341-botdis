import json, os, sys

def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ Không tìm thấy file config.json. Vui lòng tạo file cấu hình.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Lỗi đọc config.json: {e}")
        sys.exit(1)
    return config
