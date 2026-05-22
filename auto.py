import os
import json
import urllib.parse
import struct
import re

MAPS_DIR = "./maps"
COVERS_DIR = "./covers"
OUTPUT_FILE = "index.json"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/SavvyScripter-GH/savia_db/main/maps/"
GITHUB_COVER_BASE = "https://raw.githubusercontent.com/SavvyScripter-GH/savia_db/main/covers/"

if not os.path.exists(COVERS_DIR):
    os.makedirs(COVERS_DIR)

def sanitize_id(name):
    clean = name.lower()
    clean = re.sub(r'[^a-z0-9_]', '_', clean)
    return re.sub(r'_+', '_', clean).strip('_')

def get_sspm_metadata(filepath, safe_id):
    try:
        with open(filepath, "rb") as f:
            sig = f.read(4)
            if sig != b"SS+m": return None
            version = struct.unpack("<H", f.read(2))[0]
            f.read(4)

            if version == 2:
                f.seek(0x10)
                m_off, m_len = struct.unpack("<QQ", f.read(16))
                n_off, n_len = struct.unpack("<QQ", f.read(16))
                f.seek(0x30)
                c_off, c_len = struct.unpack("<QQ", f.read(16))
                
                f.seek(0x1e)
                last_ms = struct.unpack("<I", f.read(4))[0]
                note_count = struct.unpack("<I", f.read(4))[0]
                f.seek(0x2a)
                difficulty = struct.unpack("<B", f.read(1))[0] - 1
                
                f.seek(0x80)
                def read_sspm_str():
                    length = struct.unpack("<H", f.read(2))[0]
                    return f.read(length).decode('utf-8', 'ignore')

                m_id, m_name, m_song = read_sspm_str(), read_sspm_str(), read_sspm_str()
                auth_count = struct.unpack("<H", f.read(2))[0]
                authors = [read_sspm_str() for _ in range(auth_count)]

                has_cover = False
                if c_len > 0:
                    f.seek(c_off)
                    cover_data = f.read(c_len)
                    with open(f"{COVERS_DIR}/{safe_id}.png", "wb") as img:
                        img.write(cover_data)
                    has_cover = True

                return {
                    "id": m_id, "name": m_name, "song": m_song, "author": authors,
                    "difficulty": difficulty, "note_count": note_count, "length_ms": last_ms,
                    "m_off": m_off, "m_len": m_len, "n_off": n_off, "n_len": n_len,
                    "has_cover": has_cover
                }
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    return None

def main():
    new_index = {}
    files = [f for f in os.listdir(MAPS_DIR) if f.endswith(".sspm")]
    for filename in files:
        file_path = os.path.join(MAPS_DIR, filename)
        safe_id = sanitize_id(filename[:-5])
        meta = get_sspm_metadata(file_path, safe_id)
        
        if meta:
            new_index[safe_id] = {
                "id": safe_id,
                "name": meta["name"],
                "author": meta["author"],
                "download": GITHUB_RAW_BASE + urllib.parse.quote(filename),
                "cover": GITHUB_COVER_BASE + safe_id + ".png" if meta["has_cover"] else "",
                "has_cover": meta["has_cover"],
                "difficulty": max(0, meta["difficulty"]),
                "note_count": meta["note_count"],
                "music_offset": meta["m_off"],
                "music_length": meta["m_len"],
                "note_data_offset": meta["n_off"],
                "note_data_length": meta["n_len"]
            }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(new_index, f, indent=2)

if __name__ == "__main__":
    main()