#!/usr/bin/env python3
import sqlite3

def check_schema():
    conn = sqlite3.connect("disability_findings.db")
    cursor = conn.cursor()
    
    # Get table info
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("Tables in database:")
    for table in tables:
        print(f"  {table[0]}")
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"    {col[1]} ({col[2]})")
        print()
    
    conn.close()

if __name__ == "__main__":
    check_schema()