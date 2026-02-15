import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, send_from_directory

from db import get_filter_options, get_game, init_db, list_games

app = Flask(__name__, template_folder="templates", static_folder="static")

init_db()


@app.route("/")
def index():
    # Get query parameters
    page = request.args.get("page", 1, type=int)
    sort_by = request.args.get("sort_by", "id")
    sort_order = request.args.get("sort_order", "asc")

    # Filter parameters
    model = request.args.get("model") or None
    word = request.args.get("word") or None
    solved = request.args.get("solved")
    error = request.args.get("error")

    # Convert boolean filters - handle empty strings as None
    if solved:
        solved = solved.lower() == "true"
    else:
        solved = None
    if error:
        error = error.lower() == "true"
    else:
        error = None

    # Get games with pagination and filtering
    games, total_count = list_games(
        page=page,
        per_page=100,
        sort_by=sort_by,
        sort_order=sort_order,
        model=model,
        word=word,
        solved=solved,
        error=error,
    )

    # Get filter options
    filter_options = get_filter_options()

    # Calculate pagination
    total_pages = (total_count + 99) // 100
    has_prev = page > 1
    has_next = page < total_pages

    return render_template(
        "index.html",
        games=games,
        page=page,
        total_pages=total_pages,
        total_count=total_count,
        has_prev=has_prev,
        has_next=has_next,
        sort_by=sort_by,
        sort_order=sort_order,
        model=model,
        word=word,
        solved=solved,
        error=error,
        models=filter_options["models"],
        words=filter_options["words"],
    )


@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)


@app.route("/<int:game_id>")
def view_game(game_id):
    game = get_game(game_id)
    if game is None:
        return "Game not found", 404
    prev_game_id = game_id - 1 if game_id > 1 else None
    next_game_id = game_id + 1
    return render_template(
        "game.html",
        game=game,
        game_id=game_id,
        prev_game_id=prev_game_id,
        next_game_id=next_game_id,
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5005)
