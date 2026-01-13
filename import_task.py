# import_task.py
import json
import os
import time
from db_config import get_connection

INPUT_FILE = 'jmdict-eng-common-3.6.1.json'


def _extract_headword(word: dict) -> str:
    kanji_list = word.get('kanji') or []
    kana_list = word.get('kana') or []
    if kanji_list:
        return (kanji_list[0] or {}).get('text') or ''
    if kana_list:
        return (kana_list[0] or {}).get('text') or ''
    return ''


def _extract_reading(word: dict) -> str:
    kana_list = word.get('kana') or []
    if kana_list:
        return (kana_list[0] or {}).get('text') or ''
    return ''


def _is_common(word: dict) -> int:
    kanji_list = word.get('kanji') or []
    kana_list = word.get('kana') or []
    return 1 if any((x or {}).get('common') for x in (kanji_list + kana_list)) else 0


def _extract_gloss_text(word: dict) -> str:
    """Flatten English gloss into a single text field for search."""
    glosses: list[str] = []
    for sense in word.get('sense') or []:
        for gloss in sense.get('gloss') or []:
            # JMdict JSON uses objects like: {"lang":"eng", "text":"..."}
            if isinstance(gloss, dict):
                if gloss.get('lang') and gloss.get('lang') != 'eng':
                    continue
                text = gloss.get('text')
                if text:
                    glosses.append(str(text))
            elif isinstance(gloss, str):
                # fallback if dataset shape differs
                glosses.append(gloss)

    # de-dup while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for g in glosses:
        if g not in seen:
            seen.add(g)
            unique.append(g)
    return '; '.join(unique)

def run_import():
    if not os.path.exists(INPUT_FILE):
        print(f"Không tìm thấy file '{INPUT_FILE}' trong thư mục.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    words_list = data.get('words', [])
    total_words = len(words_list)
    print(f"Found {total_words} words. Starting import...")

    sql_insert = """
        INSERT INTO dictionary (id, headword, reading, is_common, gloss_text, raw_json)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    batch_data = []
    count = 0
    start_time = time.time()

    for word in words_list:
        w_id = word.get('id')

        headword = _extract_headword(word)
        reading = _extract_reading(word)
        is_common = _is_common(word)
        gloss_text = _extract_gloss_text(word)
        raw_json = json.dumps(word, ensure_ascii=False)

        row = (w_id, headword, reading, is_common, gloss_text, raw_json)
        batch_data.append(row)
        count += 1
        
        if len(batch_data) >= 1000:
            cursor.executemany(sql_insert, batch_data)
            conn.commit()
            batch_data = []
            print(f"   -> Imported {count}/{total_words} words...")

    if batch_data:
        cursor.executemany(sql_insert, batch_data)
        conn.commit()

    cursor.execute("SELECT COUNT(*) FROM dictionary")
    imported_count = cursor.fetchone()[0]

    duration = time.time() - start_time
    rate = (count / duration) if duration > 0 else 0
    print(f"Imported {count} words in {duration:.2f} seconds (~{rate:,.0f} words/second).")
    print(f"Check in DB: {imported_count}/{total_words} records.")
    if imported_count != total_words:
        print(" Warning: number of records in DB does not match number of words in file.")
    
    cursor.close()
    conn.close()