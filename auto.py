import os
import json
import urllib.parse
import struct
import re

MAPS_DIR = "./maps"
OUTPUT_FILE = "index.json"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/SavvyScripter-GH/savia_db/main/maps/"

def sanitize_id(name):
    #clean = name.lower()
    #clean = re.sub(r'[^a-z0-9_]', '_', clean)
    #clean = re.sub(r'_+', '_', clean)
    return name#clean.strip('_')

def get_sspm_metadata(filepath):
    try:
        with open(filepath, "rb") as f:
            sig = f.read(4)
            if sig != b"SS+m": return None
            
            version = struct.unpack("<H", f.read(2))[0]
            f.read(4)

            if version == 1:
                f.seek(10)
                data = f.read().decode('utf-8', 'ignore').split('\n')
                return {"id": data[0], "name": data[1], "author": [data[2]], "v": 1}
            
            elif version == 2:
                f.seek(0x10)
                music_offset = struct.unpack("<Q", f.read(8))[0]
                music_length = struct.unpack("<Q", f.read(8))[0]
                note_offset = struct.unpack("<Q", f.read(8))[0]
                note_length = struct.unpack("<Q", f.read(8))[0]
                
                f.seek(0x1e)
                last_ms = struct.unpack("<I", f.read(4))[0]
                note_count = struct.unpack("<I", f.read(4))[0]
                
                f.seek(0x2a)
                difficulty = struct.unpack("<B", f.read(1))[0] - 1
                
                f.seek(0x80)
                def read_sspm_str():
                    l_bytes = f.read(2)
                    if not l_bytes: return ""
                    length = struct.unpack("<H", l_bytes)[0]
                    return f.read(length).decode('utf-8', 'ignore')

                m_id = read_sspm_str()
                m_name = read_sspm_str()
                m_song = read_sspm_str()
                
                auth_count = struct.unpack("<H", f.read(2))[0]
                authors = [read_sspm_str() for _ in range(auth_count)]

                return {
                    "id": m_id, "name": m_name, "song": m_song,
                    "author": authors, "difficulty": difficulty,
                    "note_count": note_count, "length_ms": last_ms,
                    "m_off": music_offset, "m_len": music_length,
                    "n_off": note_offset, "n_len": note_length,
                    "v": 2
                }
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    return None

def main():
    new_index = {}
    if not os.path.exists(MAPS_DIR): return

    files = [f for f in os.listdir(MAPS_DIR) if f.endswith(".sspm")]
    for filename in files:
        file_path = os.path.join(MAPS_DIR, filename)
        encoded_filename = urllib.parse.quote(filename)
        safe_id = sanitize_id(filename[:-5])
        meta = get_sspm_metadata(file_path)
        
        if meta and meta.get("v") == 2:
            new_index[safe_id] = {
                "id": safe_id,
                "name": meta["name"],
                "song": meta.get("song", meta["name"]),
                "author": meta["author"],
                "download": GITHUB_RAW_BASE + encoded_filename,
                "version": 2,
                "difficulty": max(0, meta["difficulty"]),
                "difficulty_name": "LOGIC?",
                "stars": 0,
                "note_count": meta["note_count"],
                "length_ms": meta["length_ms"],
                "music_format": "mp3",
                "music_offset": meta["m_off"],
                "music_length": meta["m_len"],
                "note_data_offset": meta["n_off"],
                "note_data_length": meta["n_len"]
            }
        else:
            new_index[safe_id] = {
                "id": safe_id,
                "name": filename[:-5].replace("_", " "),
                "download": GITHUB_RAW_BASE + encoded_filename,
                "version": 1
            }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(new_index, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()