import json

from tadawul.scraper.servlet import TadawulServlet


def main():
    servlet = TadawulServlet()

    results = servlet.fetch()

    output_path = "data/tadawul_servlet.json"

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            results,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"Saved {len(results)} records "
        f"to: {output_path}"
    )


if __name__ == "__main__":
    main()