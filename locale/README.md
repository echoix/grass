# Translation Technical Details

For instructions on how to contribute translations, please see the
[Translations section in CONTRIBUTING.md](../CONTRIBUTING.md#translations).

## Technical notes for developers

Translations from Weblate are automatically submitted to the GRASS source repository
as pull requests.

GRASS must be configured with `--with-nls` and recompiled to use translated messages.
Updating message catalogs requires a Unix-like system with `gettext` installed.

**Translation portal**: <https://weblate.osgeo.org/projects/grass-gis/>

### Interface of Python tools

Python tools declare their interface in `# %module`, `# %flag`, and `# %option`
header comments read by *g.parser*. These strings are extracted by
`grass_tool_header_pot.py` (Python standard library only, no build needed) and
merged into `templates/grassmods.pot` by `make pot`. The extracted entries refer
to the real source lines and have comments for translators telling what each
string is. Each description of an option value is a separate entry with the
`option value description` message context, as *g.parser* translates them
separately.

To check the strings of a single tool, run:

```sh
python grass_tool_header_pot.py ../scripts/r.mask/r.mask.py
```
