# Anifix

anifix is a tool for correcting anime episode titles in file names.

Many anime series are distributed with episode titles like "Episode 1 - ..." or "Episode 2 - ...", preventing Jellyfin from correctly determining the show order.

This tool corrects those titles to the format "S01E01 - ..." or "S01E02 - ...", allowing Jellyfin to sort the episodes correctly.

It does this by checking the current directory for a spec file, which contains sections, denoting which episode belongs in which series, and what episode number it should have.

## Spec file format

`anifix.spec` is a text file that defines the series and episodes:

```txt
# Season | Episode range
1 | 1-12
2 | 13-24
```

## Expected functionality

The tool should read the `anifix.spec` file and use the information to rename the episode files in the current directory. It should match the episode titles to the correct series and season.

### Sample directory structure

```
touch "Episode 1 - My First Episode.mkv"
touch "Episode 2 - My Second Episode.mkv"
touch "Episode 3 - My Third Episode.mkv"
touch "Episode 4 - My Fourth Episode.mkv"
touch "Episode 5 - My Fifth Episode.mkv"
touch "Episode 6 - My Sixth Episode.mkv"
touch "Episode 7 - My Seventh Episode.mkv"
touch "Episode 8 - My Eighth Episode.mkv"
touch "Episode 9 - My Ninth Episode.mkv"
touch "Episode 10 - My Tenth Episode.mkv"
```

### Sample `anifix.spec` file

```txt
# Season | Episode range
1 | 1-4
2 | 5-7
3 | 8-10
```

### Sample output directory after running `anifix`

```
S01E01 - My First Episode.mkv
S01E02 - My Second Episode.mkv
S01E03 - My Third Episode.mkv
S01E04 - My Fourth Episode.mkv
S02E01 - My Fifth Episode.mkv
S02E02 - My Sixth Episode.mkv
S02E03 - My Seventh Episode.mkv
S03E01 - My Eighth Episode.mkv
S03E02 - My Ninth Episode.mkv
S03E03 - My Tenth Episode.mkv
```

## `uv`

Project is managed with `uv`.

Run scripts with `uv run <script>`.
Run tools with `uv run <tool> <script/directory>`.

Use `ruff` for linting and formatting, and `mypy` for type checking.

## Format/linting warnings

The majority of linting warnings pertaining to whitespace should be ignored, as they're corrected with `ruff`.

```

```
