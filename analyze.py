import sqlite3
import json

conn = sqlite3.connect("games.db")
cursor = conn.cursor()

query = """
SELECT
    model,
    COUNT(CASE WHEN solved = TRUE AND guesses < 6 THEN 1 END) as successful_games,
    AVG(CASE WHEN solved = TRUE AND guesses < 6 THEN guesses END) as guesses_per_game_avg
FROM games
GROUP BY model
ORDER BY 2 DESC
"""

cursor.execute(query)
result = cursor.fetchall()

# Convert to list of dictionaries
data = []
for row in result:
    data.append(
        {
            "model": row[0],
            "successful_games": row[1],
            "guesses_per_game_avg": round(row[2], 2) if row[2] is not None else None,
        }
    )

# Write to JSON file
with open("results.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"Wrote {len(data)} records to site/results.json")

conn.close()
