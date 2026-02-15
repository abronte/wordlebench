#!/usr/bin/env python3
"""Generate table HTML from results.json and insert into site/index.html"""

import json
from pathlib import Path


def get_rank_class(rank):
    """Return the CSS class for a given rank."""
    if rank == 1:
        return "rank-1"
    elif rank == 2:
        return "rank-2"
    elif rank == 3:
        return "rank-3"
    else:
        return "rank-other"


def generate_table_row(data, rank):
    """Generate a single table row from result data."""
    model_parts = data["model"].split("/")
    provider = model_parts[0] if len(model_parts) > 1 else "unknown"
    model_name = model_parts[1] if len(model_parts) > 1 else data["model"]

    success_rate = data["successful_games"]
    avg_guesses = data["guesses_per_game_avg"]
    avg_cost = data["avg_cost_per_game"]

    rank_class = get_rank_class(rank)

    return f"""                        <tr>
                            <td><span class="badge-rank {rank_class}">{rank}</span></td>
                            <td><span class="model-name">{model_name}</span></td>
                            <td><span class="provider-badge">{provider}</span></td>
                            <td>
                                <div class="d-flex align-items-center">
                                    <div class="progress flex-grow-1" style="height: 8px; max-width: 100px;">
                                        <div class="progress-bar progress-bar-custom" role="progressbar" style="width: {success_rate}%"></div>
                                    </div>
                                    <span class="ms-2">{success_rate}%</span>
                                </div>
                            </td>
                            <td>{avg_guesses}</td>
                            <td>${avg_cost:.2f}</td>
                        </tr>"""


def generate_table_body(results):
    """Generate the full table body from results data."""
    rows = []

    # Sort by successful_games descending
    sorted_results = sorted(results, key=lambda x: x["successful_games"], reverse=True)

    for i, result in enumerate(sorted_results):
        rank = i + 1  # Simple sequential ranking
        rows.append(generate_table_row(result, rank))

    return "\n".join(rows)


def generate_failed_words_table(failed_words):
    """Generate the failed words table body."""
    rows = []

    for i, word_data in enumerate(failed_words):
        rank = i + 1
        word = word_data.get("word", "")

        rank_class = get_rank_class(rank)

        row = f"""                        <tr>
                            <td><span class="badge-rank {rank_class}">{rank}</span></td>
                            <td><span class="model-name">{word}</span></td>
                        </tr>"""
        rows.append(row)

    return "\n".join(rows)


def replace_table_content(content, start_marker, end_marker, new_body):
    """Replace content between markers with new table body."""
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print(f"Error: Could not find {start_marker} in index.html")
        return None

    end_idx = content.find(end_marker, start_idx + len(start_marker))
    if end_idx == -1:
        print(f"Error: Could not find {end_marker} in index.html")
        return None

    # Replace the content between the markers
    return (
        content[: start_idx + len(start_marker)]
        + "\n"
        + new_body
        + "\n                    "
        + content[end_idx:]
    )


def main():
    # Read results.json
    results_path = Path("results.json")
    with open(results_path, "r") as f:
        results = json.load(f)

    # Read failed_words.json
    failed_words_path = Path("failed_words.json")
    with open(failed_words_path, "r") as f:
        failed_words = json.load(f)

    # Generate table body HTML
    table_body = generate_table_body(results)
    failed_words_body = generate_failed_words_table(failed_words)

    # Read index.html
    index_path = Path("site/index.html")
    with open(index_path, "r") as f:
        content = f.read()

    # Replace leaderboard table
    content = replace_table_content(
        content, '<tbody id="tableBody">', "</tbody>", table_body
    )
    if content is None:
        return

    # Replace failed words table
    content = replace_table_content(
        content, '<tbody id="failedWordsBody">', "</tbody>", failed_words_body
    )
    if content is None:
        return

    # Write the updated index.html
    with open(index_path, "w") as f:
        f.write(content)

    print(f"✓ Updated {index_path} with {len(results)} leaderboard rows")
    print(f"✓ Updated {index_path} with {len(failed_words)} failed words")


if __name__ == "__main__":
    main()
