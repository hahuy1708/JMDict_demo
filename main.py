# main.py
import sys
import db_config
import import_task
import search

def main_menu():
    try:
        db_config.setup_database()
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return

    while True:
        print("\n" + "="*30)
        print("   JAPANESE - ENGLISH DICTIONARY (CONSOLE)")
        print("="*30)
        print("1. Import Data (Run once initially)")
        print("2. Search")
        print("3. Exit")
        
        choice = input(" Choose an option (1-3): ").strip()

        if choice == '1':
            confirm = input(" This will delete old data and re-import. Continue? (y/n): ")
            if confirm.lower() == 'y':
                import_task.run_import()
        
        elif choice == '2':
            keyword = input("Enter the word to search (Eng/Kanji/Hiragana): ").strip()
            if keyword:
                search.perform_search(keyword)
        
        elif choice == '3':
            sys.exit()
        
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main_menu()