from __future__ import annotations

import json
import time
from pathlib import Path

import dlt

from tadawul.scraper.mutual_fund import MutualFundScraper


PROGRESS_PATH = Path(
    "data/mutual_fund_pipeline_progress.json"
)

LANGUAGES = ["en", "ar"]

MAX_LOAD_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5


@dlt.resource(
    name="raw_mutual_fund",
    write_disposition="merge",
    primary_key=["symbol", "language"],
)
def mutual_fund_resource(result: dict):
    yield result


def load_progress() -> set[tuple[str, str]]:
    """Load successfully completed symbol/language pairs."""

    if not PROGRESS_PATH.exists():
        return set()

    with PROGRESS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return {
        (str(item["symbol"]), item["language"])
        for item in data.get("completed", [])
    }


def save_progress(
    completed: set[tuple[str, str]],
) -> None:
    """Persist completed pairs so a future run can resume."""

    PROGRESS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = PROGRESS_PATH.with_suffix(".tmp")

    data = {
        "completed": [
            {
                "symbol": symbol,
                "language": language,
            }
            for symbol, language in sorted(completed)
        ]
    }

    with temporary_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

    temporary_path.replace(PROGRESS_PATH)


def main():
    pipeline = dlt.pipeline(
        pipeline_name="tadawul_mutual_fund",
        destination="postgres",
        dataset_name="raw_tadawul",
    )

    completed = load_progress()

    print(
        f"Previously completed pairs: {len(completed)}"
    )

    failed_scrapes: list[tuple[str, str, str]] = []

    # Retry pending dlt packages before scraping new records.
    # If the database is still unavailable, stop without
    # creating more pending work.
    print("\nChecking for pending dlt packages...")

    try:
        pending_load_info = pipeline.load()

        if pending_load_info is not None:
            print(pending_load_info)

        print("Pending package check finished.")

    except Exception as exc:
        print("\nFAILED to load pending dlt package(s).")
        print(exc)
        print(
            "\nStopping before scraping new records. "
            "Fix the database connection and rerun."
        )
        raise

    # First discover the symbols in each language so that
    # the total progress count is known before scraping.
    symbols_by_language: dict[str, list[str]] = {}

    for language in LANGUAGES:
        print(
            f"\nDiscovering mutual fund symbols - "
            f"{language.upper()}"
        )

        try:
            with MutualFundScraper(
                headless=True,
                language=language,
            ) as scraper:
                symbols = scraper.get_all_fund_symbols()

        except Exception as exc:
            print(
                f"Failed to retrieve mutual fund symbols "
                f"for {language}: {exc}"
            )
            raise

        symbols_by_language[language] = list(
            dict.fromkeys(
                str(symbol)
                for symbol in symbols
            )
        )

        print(
            f"Found {len(symbols_by_language[language])} "
            f"mutual funds - {language}"
        )

    total_tasks = sum(
        len(symbols_by_language[language])
        for language in LANGUAGES
    )

    # Count only completed pairs that belong to the current
    # workload. The progress file may contain older symbols.
    already_completed = sum(
        1
        for language in LANGUAGES
        for symbol in symbols_by_language[language]
        if (symbol, language) in completed
    )

    print("\n" + "=" * 60)
    print("MUTUAL FUND PIPELINE")
    print("=" * 60)
    print(f"Total symbol-language tasks: {total_tasks}")
    print(f"Already completed tasks: {already_completed}")
    print(
        f"Remaining tasks: "
        f"{total_tasks - already_completed}"
    )
    print("=" * 60)

    task_number = 0

    # Process all English funds first, then all Arabic funds.
    for language in LANGUAGES:
        symbols = symbols_by_language[language]

        print("\n" + "=" * 60)
        print(f"STARTING {language.upper()} MUTUAL FUNDS")
        print("=" * 60)

        with MutualFundScraper(
            headless=True,
            language=language,
        ) as scraper:

            for symbol in symbols:
                task_number += 1
                pair = (symbol, language)
                progress = f"[{task_number}/{total_tasks}]"

                if pair in completed:
                    print(
                        f"{progress} Already completed: "
                        f"{symbol} - {language}; skipping"
                    )
                    continue

                print(
                    f"\n{progress} Scraping mutual fund "
                    f"{symbol} - {language}"
                )

                # Scrape separately from dlt so scraper errors
                # are not confused with database load errors.
                try:
                    result = scraper.scrape(symbol)

                    if not isinstance(result, dict):
                        raise TypeError(
                            "Scraper did not return a dictionary"
                        )

                    result["symbol"] = symbol
                    result["language"] = language

                except Exception as exc:
                    print(
                        f"{progress} SCRAPE FAILED: "
                        f"{symbol} - {language}: {exc}"
                    )

                    failed_scrapes.append(
                        (symbol, language, str(exc))
                    )

                    # Continue to the next fund. This pair
                    # remains incomplete and can be retried
                    # on a future run.
                    continue

                # Retry database/load errors. If every attempt
                # fails, stop to avoid processing new records
                # while the current dlt package is pending.
                for attempt in range(
                    1,
                    MAX_LOAD_ATTEMPTS + 1,
                ):
                    try:
                        load_info = pipeline.run(
                            mutual_fund_resource(result)
                        )

                        print(load_info)

                        # Record progress only after run()
                        # returns successfully.
                        completed.add(pair)
                        save_progress(completed)

                        print(
                            f"{progress} COMPLETED: "
                            f"{symbol} - {language}"
                        )

                        break

                    except Exception as exc:
                        print(
                            f"{progress} LOAD FAILED: "
                            f"{symbol} - {language}; "
                            f"attempt "
                            f"{attempt}/{MAX_LOAD_ATTEMPTS}"
                        )
                        print(exc)

                        if attempt == MAX_LOAD_ATTEMPTS:
                            print(
                                "\nStopping pipeline to preserve "
                                "the pending dlt package. Fix the "
                                "database/load issue and rerun."
                            )
                            raise

                        print(
                            f"Retrying in "
                            f"{RETRY_DELAY_SECONDS} seconds..."
                        )
                        time.sleep(RETRY_DELAY_SECONDS)

        print(
            f"\nFinished {language.upper()} mutual funds."
        )

    # Final summary
    tasks = [
        (symbol, language)
        for language in LANGUAGES
        for symbol in symbols_by_language[language]
    ]

    finished_tasks = sum(
        1
        for symbol, language in tasks
        if (symbol, language) in completed
    )

    print("\n" + "=" * 60)
    print("MUTUAL FUND PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Total tasks: {total_tasks}")
    print(f"Completed tasks: {finished_tasks}")
    print(
        f"Remaining tasks: "
        f"{total_tasks - finished_tasks}"
    )
    print(
        f"Scraping failures this run: "
        f"{len(failed_scrapes)}"
    )

    if failed_scrapes:
        print("\nFailed scrapes:")

        for symbol, language, error in failed_scrapes:
            print(
                f"  {symbol} - {language}: {error}"
            )

        print(
            "\nThese pairs remain incomplete and will be "
            "retried on a future run."
        )


if __name__ == "__main__":
    main()