import sqlite3
import json

conn = sqlite3.connect("games.db")
cursor = conn.cursor()

query = """
SELECT
    model,
    COUNT(CASE WHEN solved = TRUE AND guesses < 6 THEN 1 END) as successful_games,
    AVG(CASE WHEN solved = TRUE AND guesses < 6 THEN guesses END) as guesses_per_game_avg,
    AVG(cost) as avg_cost_per_game
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
            "avg_cost_per_game": round(row[3], 2) if row[3] is not None else None,
        }
    )

# Write to JSON file
with open("results.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"Wrote {len(data)} records to site/results.json")

# Query for hardest words (most unsolved)
query2 = """
SELECT
    word,
    COUNT(CASE WHEN solved = 0 THEN 1 END) as failure_count
FROM games
GROUP BY word
ORDER BY failure_count DESC
LIMIT 10
"""

cursor.execute(query2)
result2 = cursor.fetchall()

# Convert to list of dictionaries
hardest_words = []
for row in result2:
    hardest_words.append({"word": row[0]})

# Write to JSON file
with open("failed_words.json", "w") as f:
    json.dump(hardest_words, f, indent=2)

print(f"Wrote {len(hardest_words)} records to failed_words.json")

conn.close()
