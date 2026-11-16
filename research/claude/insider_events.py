"""Open-market insider purchases from the SEC's Insider Transactions Data Sets
(strategies/insider_buying/HYPOTHESIS.md): one row per company, filing date and insider.

    uv run python research/claude/insider_events.py
"""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

import duckdb

from kinn.core.settings import load_settings

TABLES = ("SUBMISSION", "REPORTINGOWNER", "NONDERIV_TRANS")


def main() -> None:
    settings = load_settings()
    raw = settings.raw_dir / "sec" / "insiders"
    out = settings.data_dir / "research" / "insider"
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("set threads=3; set memory_limit='1500MB'")
    parts = []
    for path in sorted(raw.glob("*_form345.zip")):
        with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(path) as z:
            for name in TABLES:
                z.extract(f"{name}.tsv", tmp)
            read = "read_csv('{}/{}.tsv', delim='\t', header=true, all_varchar=true, quote='')"
            con.execute(
                f"""create or replace table q as
                    with t as (
                        select ACCESSION_NUMBER as a,
                               sum(try_cast(TRANS_SHARES as double)
                                   * try_cast(TRANS_PRICEPERSHARE as double)) as dollars,
                               sum(try_cast(TRANS_SHARES as double)) as shares,
                               max(try_strptime(TRANS_DATE, '%d-%b-%Y')::date) as traded
                        from {read.format(tmp, "NONDERIV_TRANS")}
                        where TRANS_CODE = 'P' and TRANS_ACQUIRED_DISP_CD = 'A'
                          and try_cast(TRANS_SHARES as double) > 0
                          and try_cast(TRANS_PRICEPERSHARE as double) between 0.01 and 100000
                        group by 1),
                    o as (select ACCESSION_NUMBER as a, min(RPTOWNERCIK) as owner,
                                 bool_or(RPTOWNER_RELATIONSHIP ilike '%officer%') as officer,
                                 bool_or(RPTOWNER_RELATIONSHIP ilike '%director%') as director,
                                 bool_or(RPTOWNER_RELATIONSHIP ilike '%tenpercent%') as ten,
                                 any_value(RPTOWNER_TITLE) as title
                          from {read.format(tmp, "REPORTINGOWNER")} group by 1)
                    select upper(trim(s.ISSUERTRADINGSYMBOL)) as symbol, s.ISSUERCIK as cik,
                           try_strptime(s.FILING_DATE, '%d-%b-%Y')::date as filed, t.traded,
                           o.owner, o.officer, o.director, o.ten, o.title, t.dollars, t.shares,
                           s.ACCESSION_NUMBER as accession
                    from {read.format(tmp, "SUBMISSION")} s join t on t.a = s.ACCESSION_NUMBER
                    join o on o.a = s.ACCESSION_NUMBER
                    where s.DOCUMENT_TYPE = '4'"""
            )
            part = Path(tmp) / "part.parquet"
            con.execute(f"copy q to '{part}' (format parquet)")
            parts.append(con.sql(f"select * from '{part}'").to_arrow_table())
        print(path.name, parts[-1].num_rows, flush=True)
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pa.concat_tables(parts)
    pq.write_table(table, out / "purchases.parquet")
    con.register("p", table)
    print(
        con.sql("""select year(filed) as yr, count(*) as filings, count(distinct symbol) as companies,
                            round(median(dollars)) as median_dollars,
                            round(avg((date_diff('day', traded, filed) <= 10)::int), 3) as timely,
                            round(avg(officer::int), 2) as officer, round(avg(ten::int), 2) as ten
                     from p group by 1 order by 1""").fetchall()
    )


if __name__ == "__main__":
    main()
