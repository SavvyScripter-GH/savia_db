import os
import json
import urllib.parse
import struct
import re

MAPS_DIR = "./maps"
OUTPUT_FILE = "index.json"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/SavvyScripter-GH/savia_db/main/maps/"

def sanitize_id(name):
    clean = name.lower()
    clean = re.sub(r'[^a-z0-9_]', '_', clean)
    clean = re.sub(r'_+', '_', clean)
    return clean.strip('_')

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
                return {"id": data[0], "name": data[1], "author": [data[2]]}
            
            elif version == 2:
                f.seek(0x1e)
                last_ms = struct.unpack("<I", f.read(4))[0]
                note_count = struct.unpack("<I", f.read(4))[0]
                f.seek(0x2a)
                difficulty = struct.unpack("<B", f.read(1))[0] - 1
                
                f.seek(0x80)
                def read_sspm_str():
                    length = struct.unpack("<H", f.read(2))[0]
                    return f.read(length).decode('utf-8', 'ignore')

                m_id = read_sspm_str()
                m_name = read_sspm_str()
                m_song = read_sspm_str()
                
                auth_count = struct.unpack("<H", f.read(2))[0]
                authors = [read_sspm_str() for _ in range(auth_count)]

                return {
                    "id": m_id, "name": m_name, "song": m_song,
                    "author": authors, "difficulty": difficulty,
                    "note_count": note_count, "length_ms": last_ms
                }
    except Exception as e:
        print(f"Could not parse binary for {filepath}: {e}")
    return None

def main():
    new_index = {}

    if not os.path.exists(MAPS_DIR):
        print(f"Error: Folder '{MAPS_DIR}' not found")
        return

    files = [f for f in os.listdir(MAPS_DIR) if f.endswith(".sspm")]
    print(f"Found {len(files)} maps locally.")

    for filename in files:
        file_path = os.path.join(MAPS_DIR, filename)
        
        encoded_filename = urllib.parse.quote(filename)
        
        meta = get_sspm_metadata(file_path)
        
        safe_id = sanitize_id(filename[:-5])
        
        if meta:
            difficulty = 0 if meta.get("difficulty", 4) == -1 else meta.get("difficulty", 4)
            new_index[safe_id] = {
                "id": safe_id,
                "name": meta["name"],
                "song": meta.get("song", meta["name"]),
                "author": meta["author"],
                "download": GITHUB_RAW_BASE + encoded_filename,
                "version": 1,
                "difficulty": difficulty,
                "difficulty_name": "LOGIC?",
                "stars": 0,
                "has_cover": False,
                "tags": ["ss_archive"],
                "broken": False,
                "note_count": meta.get("note_count", 0),
                "length_ms": meta.get("length_ms", 0),
                "music_format": "mp3",
                "music_offset": 0
            }
        else:
            new_index[safe_id] = {
                "id": safe_id,
                "name": filename[:-5].replace("_", " "),
                "download": GITHUB_RAW_BASE + encoded_filename,
                "tags": ["ss_archive"]
            }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(new_index, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully generated {OUTPUT_FILE} with {len(new_index)} entries.")

if __name__ == "__main__":
    main()