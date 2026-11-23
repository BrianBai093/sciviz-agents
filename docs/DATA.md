# Data: Columbia University publications, 2021-2024 (OpenAlex snapshot of 2026-11-23)

Works (papers, preprints, books, datasets, ...) published 2021-2024 with at least one author affiliated with Columbia University (OpenAlex institution I78577930 and its OpenAlex child institutions: NASA GISS, Lamont-Doherty Earth Observatory, ICAP, CZ Biohub NY), taken from the OpenAlex API on 2026-11-23 and never refreshed. Includes all co-authors and their institutions, the OpenAlex topic hierarchy, profiles of Columbia-affiliated authors, venues, outgoing references, yearly citation counts, keywords and funders.

## Scope exclusions

- Works with more than 100 authors are excluded entirely.
- Columbia University Irving Medical Center (OpenAlex I2799503643) is a separate OpenAlex institution and is NOT part of this scope unless a paper also lists Columbia University itself.
- Affiliated but separate colleges (e.g. Barnard College, Teachers College) are not included unless a paper also lists Columbia University itself.

## Caveats

- Author identities come from OpenAlex's algorithmic disambiguation; common names can be split or merged.
- Topics, subfields, fields and domains are assigned by OpenAlex's classifier and can be wrong.
- Citation counts (cited_by_count, work_citations_by_year) are as of the snapshot date; newer works have had less time to be cited.
- citations lists every outgoing reference; only rows with cited_in_snapshot = true point to works that are themselves in this dataset (and therefore have metadata here).
- authors contains profiles only for authors who are Columbia-affiliated on at least one work in the snapshot; other co-authors appear only in authorships (name and id).
- Profile metrics in authors and sources (works_count, cited_by_count, h_index, ...) are global OpenAlex values for the whole career / whole venue, not restricted to this snapshot.
- Some works have no abstract (abstract is NULL), no topic, or no source.

## Counting rules

- authorships has one row per (work, author); count works with count(DISTINCT work_id) after joining it.
- authorships.is_columbia is true when that author lists a Columbia institution on that specific work.
- A work can have up to 3 topics in work_topics; works.primary_topic_* gives the single primary one.
- work_topics joins to topics for the full hierarchy domain > field > subfield > topic.

## Tables

| Table | Rows | Description |
|---|---:|---|
| `authors` | 29,518 | Profiles of authors who are Columbia-affiliated on at least one snapshot work. |
| `authorship_institutions` | 619,528 | Institutions listed by each author on each work (an author can list several). |
| `authorships` | 438,156 | One row per (work, author) in byline order, including non-Columbia co-authors. |
| `citations` | 2,322,878 | Outgoing references of snapshot works (one row per citing -> cited pair). |
| `institutions` | 15,410 | Every institution that appears in the authorships of the snapshot works. |
| `snapshot_meta` | 6 | Provenance of the snapshot (date, filter, scope) as key/value pairs. |
| `sources` | 9,465 | Venues (journals, repositories, conferences, book series) that are the primary location of snapshot works. |
| `topics` | 4,516 | The full OpenAlex topic hierarchy (domain > field > subfield > topic), not only topics used here. |
| `work_citations_by_year` | 155,356 | Citations received by each work per calendar year (as reported by OpenAlex). |
| `work_funders` | 120,254 | Funders acknowledged by each work. |
| `work_keywords` | 468,258 | Keywords that OpenAlex extracted for each work, with a relevance score. |
| `work_topics` | 165,198 | Topics assigned to each work (up to 3), with the classifier's score. |
| `works` | 55,371 | One row per work in the snapshot. |

### `authors`

Profiles of authors who are Columbia-affiliated on at least one snapshot work.

| Column | Type | Nulls | Distinct | Description |
|---|---|---:|---:|---|
| `author_id` | VARCHAR | 0.0% | 30,686 | OpenAlex author id. Primary key. |
| `name` | VARCHAR | 0.0% | 28,388 | Display name. |
| `orcid` | VARCHAR | 32.7% | 19,196 | ORCID URL when known. |
| `works_count` | BIGINT | 0.0% | 959 | Total works in OpenAlex over the whole career (global). |
| `cited_by_count` | BIGINT | 0.0% | 7,248 | Total citations over the whole career (global). |
| `h_index` | BIGINT | 0.0% | 193 | h-index (global). |
| `i10_index` | BIGINT | 0.0% | 592 | i10-index (global). |
| `two_year_mean_citedness` | DOUBLE | 0.0% | 4,192 | Mean citations per work over the last two years (global). |
| `last_known_institutions` | VARCHAR | 0.0% | 10,067 | Names of the author's most recent institutions, separated by "; ". |
| `works_in_snapshot` | BIGINT | 0.0% | 119 | Number of snapshot works on which the author is Columbia-affiliated. |

### `authorship_institutions`

Institutions listed by each author on each work (an author can list several).

| Column | Type | Nulls | Distinct | Description |
|---|---|---:|---:|---|
| `work_id` | VARCHAR | 0.0% | 55,410 | Work id. |
| `author_order` | BIGINT | 0.0% | 102 | Byline position; together with work_id identifies the authorship. |
| `author_id` | VARCHAR | 3.6% | 175,829 | Author id. |
| `institution_id` | VARCHAR | 0.0% | 14,855 | OpenAlex institution id (joins institutions.institution_id). |

### `authorships`

One row per (work, author) in byline order, including non-Columbia co-authors.

| Column | Type | Nulls | Distinct | Description |
|---|---|---:|---:|---|
| `work_id` | VARCHAR | 0.0% | 55,410 | Work id (joins works.work_id). |
| `author_order` | BIGINT | 0.0% | 102 | 0-based position in the byline. |
| `author_id` | VARCHAR | 4.1% | 184,995 | OpenAlex author id (may be NULL for unresolved authors). |
| `author_name` | VARCHAR | 0.0% | 185,302 | Author display name. |
| `author_position` | VARCHAR | 0.0% | 3 | first, middle or last. |
| `is_corresponding` | BOOLEAN | 0.0% | 2 | True if marked as corresponding author. |
| `is_columbia` | BOOLEAN | 0.0% | 2 | True if this author lists a Columbia institution on this work. |

### `citations`

Outgoing references of snapshot works (one row per citing -> cited pair).

| Column | Type | Nulls | Distinct | Description |
|---|---|---:|---:|---|
| `citing_work_id` | VARCHAR | 0.0% | 46,289 | The snapshot work that cites (joins works.work_id). |
| `cited_work_id` | VARCHAR | 0.0% | 1,444,362 | The referenced work's OpenAlex id. |
| `cited_in_snapshot` | BOOLEAN | 0.0% | 2 | True if the cited work is also in this snapshot. |

### `institutions`

Every institution that appears in the authorships of the snapshot works.

| Column | Type | Nulls | Distinct | Description |
|---|---|---:|---:|---|
| `institution_id` | VARCHAR | 0.0% | 14,855 | OpenAlex institution id. Primary key. |
| `name` | VARCHAR | 0.0% | 14,558 | Institution name. |
| `country_code` | VARCHAR | 0.0% | 186 | ISO 3166-1 alpha-2 country code. |
| `type` | VARCHAR | 0.0% | 9 | Institution type (education, healthcare, company, government, facility, nonprofit, ...). |
| `ror` | VARCHAR | 0.0% | 15,575 | ROR identifier URL. |
| `is_columbia` | BOOLEAN | 0.0% | 2 | True for Columbia University and its OpenAlex child institutions. |

### `snapshot_meta`

Provenance of the snapshot (date, filter, scope) as key/value pairs.

| Column | Type | Nulls | Distinct | Description |
|---|---|---:|---:|---|
| `key` | VARCHAR | 0.0% | 6 | Property name. |
| `value` | VARCHAR | 0.0% | 6 | Property value. |

### `sources`

Venues (journals, repositories, conferences, book series) that are the primary location of snapshot works.

| Column | Type | Nulls | Distinct | Description |
|---|---|---:|---:|---|
| `source_id` | VARCHAR | 0.0% | 9,766 | OpenAlex source id. Primary key. |
| `name` | VARCHAR | 0.0% | 9,440 | Venue name. |
| `type` | VARCHAR | 0.0% | 6 | journal, repository, conference, ebook platform, book series, ... |
| `issn_l` | VARCHAR | 8.8% | 8,703 | Linking ISSN. |
| `publisher` | VARCHAR | 6.0% | 1,296 | Host organization / publisher name. |
| `country_code` | VARCHAR | 11.9% | 88 | Country of the venue. |
| `is_oa` | BOOLEAN | 0.0% | 2 | True if the venue is fully open access. |
| `works_count` | BIGINT | 0.0% | 5,454 | Works published in the venue (global). |
| `cited_by_count` | BIGINT | 0.0% | 9,022 | Citations to the venue's works (global). |
| `h_index` | BIGINT | 0.0% | 580 | Venue h-index (global). |

### `topics`

The full OpenAlex topic hierarchy (domain > field > subfield > topic), not only topics used here.

| Column | Type | Nulls | Distinct | Description |
|---|---|---:|---:|---|
| `topic_id` | VARCHAR | 0.0% | 4,606 | OpenAlex topic id. Primary key. |
| `topic` | VARCHAR | 0.0% | 4,724 | Topic name. |
| `subfield_id` | VARCHAR | 0.0% | 254 | Subfield id. |
| `subfield` | VARCHAR | 0.0% | 247 | Subfield name. |
| `field_id` | VARCHAR | 0.0% | 26 | Field id. |
| `field` | VARCHAR | 0.0% | 24 | Field name. |
| `domain_id` | VARCHAR | 0.0% | 4 | Domain id. |
| `domain` | VARCHAR | 0.0% | 4 | Domain name. |
| `description` | VARCHAR | 0.0% | 4,500 | Short description of the topic. |
| `keywords` | VARCHAR | 0.0% | 4,177 | Keywords associated with the topic, separated by "; ". |
| `works_count` | BIGINT | 0.0% | 4,396 | Number of works with this topic in all of OpenAlex (global). |

### `work_citations_by_year`

Citations received by each work per calendar year (as reported by OpenAlex).

| Column | Type | Nulls | Distinct | Description |
|---|---|---:|---:|---|
| `work_id` | VARCHAR | 0.0% | 45,883 | Work id. |
| `year` | BIGINT | 0.0% | 15 | Calendar year in which the citations were received. |
| `cited_by_count` | BIGINT | 0.0% | 438 | Citations received in that year. |

### `work_funders`

Funders acknowledged by each work.

| Column | Type | Nulls | Distinct | Description |
|---|---|---:|---:|---|
| `work_id` | VARCHAR | 0.0% | 29,698 | Work id. |
| `funder_id` | VARCHAR | 0.0% | 7,341 | OpenAlex funder id. |
| `funder_name` | VARCHAR | 0.0% | 7,327 | Funder name. |

### `work_keywords`

Keywords that OpenAlex extracted for each work, with a relevance score.

| Column | Type | Nulls | Distinct | Description |
|---|---|---:|---:|---|
| `work_id` | VARCHAR | 0.0% | 54,771 | Work id. |
| `keyword_id` | VARCHAR | 0.0% | 162,874 | OpenAlex keyword id. |
| `keyword` | VARCHAR | 0.0% | 140,392 | Keyword text. |
| `score` | DOUBLE | 0.0% | 691 | Relevance score (0-1). |

### `work_topics`

Topics assigned to each work (up to 3), with the classifier's score.

| Column | Type | Nulls | Distinct | Description |
|---|---|---:|---:|---|
| `work_id` | VARCHAR | 0.0% | 54,782 | Work id. |
| `topic_id` | VARCHAR | 0.0% | 4,000 | Topic id (joins topics.topic_id). |
| `score` | DOUBLE | 0.0% | 4,494 | Classifier confidence (0-1). |
| `is_primary` | BOOLEAN | 0.0% | 2 | True for the work's primary topic. |
| `rank` | BIGINT | 0.0% | 3 | 0-based rank of the topic for this work. |

### `works`

One row per work in the snapshot.

| Column | Type | Nulls | Distinct | Description |
|---|---|---:|---:|---|
| `work_id` | VARCHAR | 0.0% | 55,410 | OpenAlex work id (e.g. W4312345678). Primary key. |
| `doi` | VARCHAR | 1.0% | 56,562 | DOI URL when available. |
| `title` | VARCHAR | 0.0% | 54,789 | Title of the work. |
| `abstract` | VARCHAR | 26.4% | 39,384 | Abstract text rebuilt from OpenAlex's inverted index; NULL when unavailable. |
| `publication_year` | BIGINT | 0.0% | 4 | Year of publication (2021-2024). |
| `publication_date` | DATE | 0.0% | 1,384 | Publication date. |
| `type` | VARCHAR | 0.0% | 23 | OpenAlex work type (article, preprint, review, book-chapter, dataset, ...). |
| `language` | VARCHAR | 0.0% | 36 | ISO language code of the work. |
| `source_id` | VARCHAR | 1.3% | 9,766 | OpenAlex id of the primary venue (joins sources.source_id). |
| `source_name` | VARCHAR | 1.3% | 9,440 | Name of the primary venue (denormalized from sources). |
| `cited_by_count` | BIGINT | 0.0% | 645 | Number of citations received (global, as of snapshot date). |
| `fwci` | DOUBLE | 19.8% | 19,946 | Field-weighted citation impact; 1.0 means cited at the world average for similar works. |
| `citation_percentile` | DOUBLE | 19.8% | 25,092 | Citation percentile among works of the same field and year (0-1). |
| `is_top_1pct_cited` | BOOLEAN | 19.8% | 2 | True if in the top 1% most cited works of its field and year. |
| `is_top_10pct_cited` | BOOLEAN | 19.8% | 2 | True if in the top 10% most cited works of its field and year. |
| `is_oa` | BOOLEAN | 0.0% | 2 | True if the work is open access. |
| `oa_status` | VARCHAR | 0.0% | 6 | Open-access route (gold, green, hybrid, bronze, diamond, closed). |
| `referenced_works_count` | BIGINT | 0.0% | 475 | Number of outgoing references. |
| `authors_count` | BIGINT | 0.0% | 102 | Number of authors (at most 100 in this snapshot). |
| `columbia_authors_count` | BIGINT | 0.0% | 38 | Number of authors affiliated with Columbia on this work. |
| `countries_distinct_count` | BIGINT | 0.0% | 31 | Number of distinct countries among the authors' institutions. |
| `institutions_distinct_count` | BIGINT | 0.0% | 99 | Number of distinct institutions among the authors. |
| `is_retracted` | BOOLEAN | 0.0% | 1 | True if the work has been retracted. |
| `is_paratext` | BOOLEAN | 0.0% | 2 | True for front matter, tables of contents and similar non-research items. |
| `primary_topic_id` | VARCHAR | 0.6% | 3,219 | OpenAlex id of the primary topic (joins topics.topic_id). |
| `primary_topic` | VARCHAR | 0.6% | 3,332 | Name of the primary topic. |
| `primary_subfield` | VARCHAR | 0.6% | 240 | Subfield of the primary topic. |
| `primary_field` | VARCHAR | 0.6% | 24 | Field of the primary topic (26 fields in OpenAlex). |
| `primary_domain` | VARCHAR | 0.6% | 4 | Domain of the primary topic (Life, Social, Physical, Health Sciences). |

## Relationships

- `works.work_id = authorships.work_id`
- `authorships.(work_id, author_order) = authorship_institutions.(work_id, author_order)`
- `authorship_institutions.institution_id = institutions.institution_id`
- `authorships.author_id = authors.author_id`
- `works.source_id = sources.source_id`
- `works.primary_topic_id = topics.topic_id`
- `work_topics.work_id = works.work_id ; work_topics.topic_id = topics.topic_id`
- `citations.citing_work_id = works.work_id`
- `citations.cited_work_id = works.work_id`
- `work_citations_by_year.work_id = works.work_id`
- `work_keywords.work_id = works.work_id`
- `work_funders.work_id = works.work_id`

## Rebuild

```bash
# 1. download the raw snapshot (needs OPENALEX_API_KEY); the published snapshot date is 2026-11-23
python3 -I data_pipeline/fetch_openalex_snapshot.py --out <snapshot_dir> --years 2021-2024
# 2. build the database and this document
uv run python data_pipeline/build_duckdb.py --snapshot <snapshot_dir> --out data/columbia.duckdb
uv run python data_pipeline/build_catalog.py --db data/columbia.duckdb --semantics catalog/columbia_semantics.yaml --out catalog/columbia.yaml --doc docs/DATA.md
```
