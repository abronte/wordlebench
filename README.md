# WordleBench

WordleBench is a benchmark for evaluating LLMs on their ability to solve Wordle puzzles.

## Results

[https://www.wordlebench.com/](https://www.wordlebench.com/)

## Why?

Wordle is a game that consists of some strategy and logic. The LLM needs to keep track of guesses, feedback and analyze the information to make informed guesses. This makes it a good benchmark for evaluating the reasoning capabilities of LLMs.

## Methodology

- All models are run with the default settings through OpenRouter with reasoning set to high.
- A list of 100 randomly picked previous Wordle words are used as the test set for all models.
- Each game is a multi-turn interaction where the model makes a guess, receives feedback, and then makes another guess based on that feedback until it either solves the puzzle or exhausts the maximum number of allowed guesses.

## Running the Benchmark

```bash
# Install dependencies
uv sync

# Run the benchmark
uv run python main.py

# Analyze results
uv run python analyze.py
```
