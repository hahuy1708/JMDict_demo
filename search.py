# search.py
import json
from db_config import get_connection

def perform_search(keyword):
    conn = get_connection()
    cursor = conn.cursor()

    print(f"\n🔍 Đang tra cứu: '{keyword}'...")

    # Search priority:
    # 1) Exact headword / reading
    # 2) Prefix headword / reading
    # 3) Full-text (English gloss_text) then LIKE fallback
    sql_search = """
        SELECT raw_json, headword, reading, is_common,
               (headword = %s) AS exact_hw,
               (reading = %s) AS exact_rd,
               (headword LIKE %s) AS prefix_hw,
               (reading LIKE %s) AS prefix_rd,
               (gloss_text LIKE %s) AS like_gloss,
               MATCH(gloss_text) AGAINST (%s IN NATURAL LANGUAGE MODE) AS ft_score
        FROM dictionary
        WHERE headword = %s
           OR reading = %s
           OR headword LIKE %s
           OR reading LIKE %s
           OR gloss_text LIKE %s
           OR MATCH(gloss_text) AGAINST (%s IN NATURAL LANGUAGE MODE)
        ORDER BY exact_hw DESC,
                 exact_rd DESC,
                 prefix_hw DESC,
                 prefix_rd DESC,
                 is_common DESC,
                 ft_score DESC,
                 like_gloss DESC
        LIMIT 10;
    """

    prefix = f"{keyword}%"
    like = f"%{keyword}%"
    params = (
        keyword,
        keyword,
        prefix,
        prefix,
        like,
        keyword,
        keyword,
        keyword,
        prefix,
        prefix,
        like,
        keyword,
    )

    cursor.execute(sql_search, params)
    results = cursor.fetchall()
    
    if not results:
        print(" Cant found a result for your query.")
    else:
        print(f" Results:\n")

        for row in results:
            raw_json = row[0]
            if isinstance(raw_json, (bytes, bytearray)):
                raw_json = raw_json.decode('utf-8')
            word_obj = raw_json if isinstance(raw_json, dict) else json.loads(raw_json)
            display_pretty_word(word_obj)
            
    cursor.close()
    conn.close()

def display_pretty_word(word_obj):
    kanjis = [k.get('text') for k in word_obj.get('kanji', [])]
    kanas = [k.get('text') for k in word_obj.get('kana', [])]
    
    is_common = any(k.get('common') for k in word_obj.get('kanji', []) + word_obj.get('kana', []))
    common_label = "⭐ [COMMON]" if is_common else ""

    print(f"┏" + "━"*50)
    
    # Line 1: Main text (Prefer Kanji, if not available then use Kana)
    main_text = kanjis[0] if kanjis else kanas[0]
    reading = f"({kanas[0]})" if kanjis else ""
    print(f"┃ 🔤 WORD: {main_text} {reading} {common_label}")
    
    if len(kanjis) > 1 or (kanjis and len(kanas) > 1):
        others = ", ".join(kanjis[1:] + kanas[1:])
        print(f"┃  Others: {others}")
    print(f"┣" + "┄"*50)

    for i, sense in enumerate(word_obj.get('sense', []), 1):
        pos_list = sense.get('partOfSpeech', [])
        pos_text = f"[{', '.join(pos_list)}]" if pos_list else ""

        gloss_items = sense.get('gloss', [])
        gloss_texts = []
        for g in gloss_items:
            if isinstance(g, dict):
                if g.get('lang') and g.get('lang') != 'eng':
                    continue
                t = g.get('text')
                if t:
                    gloss_texts.append(str(t))
            elif isinstance(g, str):
                gloss_texts.append(g)

        glosses = ", ".join(gloss_texts)

        print(f"┃  {i}. {pos_text} {glosses}")
        if i >= 3: break 

    print(f"┗" + "━"*50)