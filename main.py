import csv
import json
import re
import random
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from openai import OpenAI

from models import Game
from db import check_game, add_game

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client - API key loaded from .env file (OPENAI_API_KEY)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENAI_API_KEY")
)

system_prompt = open("prompts/system_prompt.md").read()
user_prompt = open("prompts/user_prompt.md").read()


def extract_tag(data: str, tag: str) -> str:
    pattern = f"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, data, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def evaluate_guess(guess: str, target: str) -> str:
    guess = guess.upper()
    target = target.upper()
    result = []
    for g_char, t_char in zip(guess, target):
        if g_char == t_char:
            result.append("G")  # Green
        elif g_char in target:
            result.append("Y")  # Yellow
        else:
            result.append("B")  # Black
    return "".join(result)


def get_random_words(num: int = 1) -> list[str]:
    with open("words_full.txt", "r") as file:
        words = [line.strip() for line in file if line.strip()]
        return random.sample(words, min(num, len(words)))


def get_words() -> list[str]:
    with open("words.txt", "r") as file:
        words = [line.strip() for line in file if line.strip()]
        return words


def make_guess(messages: list[dict], model: str):
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
    )

    return resp


def play_wordle(word: str, model: str) -> Game:
    print(f"({model} {word}) Starting Wordle game")

    game = Game(model=model, word=word)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    while game.guesses <= 5:
        guess_completion = make_guess(messages, model)
        guess_content = guess_completion.choices[0].message.content
        game.cost += guess_completion.usage.cost
        messages.append({"role": "assistant", "content": guess_content})
        guess = extract_tag(guess_content, "guess").upper()

        if guess == "":
            print(f"({model} {word}) LLM failed to provide a guess. Ending game.")
            game.error = True
            game.guesses = -1
            return game

        result = evaluate_guess(guess, word)

        print(f"({model} {word}) Guess ({game.guesses}): {guess}")
        print(f"({model} {word}) Result: {result}")

        if guess == word:
            print(f"({model} {word}) Solved in {game.guesses} guesses!")
            game.solved = True
            break

        if game.guesses < 5:
            game.guesses += 1
            messages.append({"role": "user", "content": f"Result: {result}"})
        else:
            break

    game.messages = messages

    if not game.solved:
        print(f"({model} {word}) Failed to solve the wordle")
        game.guesses = 6
        game.solved = False

    return game


# main execution
if __name__ == "__main__":
    words = get_words()
    models = [
        "openai/gpt-5.2",
        "openai/gpt-5-mini",
        "openai/gpt-5-nano",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "anthropic/claude-opus-4.6",
        "anthropic/claude-sonnet-4.5",
        "anthropic/claude-haiku-4.5",
        "moonshotai/kimi-k2.5",
        "google/gemini-3-flash-preview",
        "google/gemini-3-pro-preview",
        "google/gemini-2.5-pro",
        "google/gemini-2.5-flash",
        "z-ai/glm-5",
        "z-ai/glm-4.7-flash",
        "z-ai/glm-4.7",
        "deepseek/deepseek-v3.2",
        "mistralai/mistral-large-2512",
        "mistralai/ministral-14b-2512",
    ]

    # Create all (word, model) pairs to process, filtering out existing games
    tasks = [
        (word, model)
        for model in models
        for word in words
        if not check_game(model, word)
    ]

    print(f"Found {len(tasks)} new games to play (filtered out existing games)")

    # Run play_wordle calls in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=25) as executor:
        # Submit all tasks
        future_to_task = {
            executor.submit(play_wordle, word, model): (word, model)
            for word, model in tasks
        }

        # Collect results as they complete
        for future in as_completed(future_to_task):
            word, model = future_to_task[future]
            try:
                game = future.result()
                add_game(game)
            except Exception as exc:
                print(
                    f"Task for word '{word}' with model '{model}' generated an exception: {exc}"
                )
