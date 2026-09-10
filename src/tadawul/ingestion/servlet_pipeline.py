from __future__ import annotations

import dlt

from tadawul.scraper.servlet import TadawulServlet


@dlt.resource(
    name="raw_servlet",
    write_disposition="merge",
    primary_key="symbol",
)
def servlet_resource():
    servlet = TadawulServlet()

    results = servlet.fetch()

    for record in results:
        yield record


def main():
    pipeline = dlt.pipeline(
        pipeline_name="tadawul_servlet",
        destination="postgres",
        dataset_name="raw_tadawul",
    )

    load_info = pipeline.run(
        servlet_resource()
    )

    print(load_info)


if __name__ == "__main__":
    main()