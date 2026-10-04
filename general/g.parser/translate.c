#include <stdlib.h>
#include <string.h>

#include "proto.h"

#include <grass/glocale.h>

/* Message context of the descriptions of option values. The same context
   must be used when extracting the strings, see locale/README.md. */
#define VALUE_DESCRIPTION_CONTEXT "option value description"

#if defined(HAVE_LIBINTL_H) && defined(USE_NLS)
static const char *translation_domain(void)
{
    static const char *domain;

    if (!domain) {
        domain = getenv("GRASS_TRANSLATION_DOMAIN");
        if (domain)
            G_putenv("GRASS_TRANSLATION_DOMAIN", "grassmods");
        else
            domain = PACKAGE;
    }

    return domain;
}
#endif

/* Returns translated version of a string.
   If global variable to output strings for translation is set it spits them out
 */
char *translate(const char *arg)
{
    if (arg == NULL)
        return (char *)arg;

    if (strlen(arg) == 0)
        return NULL; /* unset */

    if (*arg && translate_output) {
        fputs(arg, stdout);
        fputs("\n", stdout);
    }

#if defined(HAVE_LIBINTL_H) && defined(USE_NLS)
    return G_gettext(translation_domain(), arg);
#else
    return (char *)arg;
#endif
}

/* Returns translated version of a string with a message context (msgctxt),
   or the string itself if there is no translation.
   This is what pgettext() from GNU gettext.h does: gettext stores the
   context and the string joined by the EOT character.
 */
static const char *translate_in_context(const char *context, const char *arg)
{
#if defined(HAVE_LIBINTL_H) && defined(USE_NLS)
    char *key;
    const char *translated;

    G_asprintf(&key, "%s\004%s", context, arg);
    translated = G_gettext(translation_domain(), key);
    if (translated == key)
        translated = arg;
    G_free(key);

    return translated;
#else
    (void)context;
    return arg;
#endif
}

/* Returns translated version of the descriptions of option values given as
   "value;description;value;description...".
   Each description is translated separately, so the values are never part of
   the translatable strings. As in G_parser(), an unpaired trailing item is
   ignored (and kept as is).
 */
char *translate_descriptions(const char *arg)
{
    char **tokens;
    const char **items;
    char **stripped;
    char *result;
    int i, count;
    int size = 1;

    if (arg == NULL)
        return (char *)arg;

    if (strlen(arg) == 0)
        return NULL; /* unset */

    tokens = G_tokenize(arg, ";");
    count = G_number_of_tokens(tokens);
    items = G_malloc(count * sizeof(char *));
    stripped = G_calloc(count, sizeof(char *));

    for (i = 0; i < count; i++) {
        items[i] = tokens[i];
        if (i % 2 == 1) {
            const char *translated;

            stripped[i] = G_store(tokens[i]);
            G_strip(stripped[i]);
            if (*stripped[i] && translate_output) {
                fputs(stripped[i], stdout);
                fputs("\n", stdout);
            }
            translated =
                translate_in_context(VALUE_DESCRIPTION_CONTEXT, stripped[i]);
            /* A semicolon would split the translation into more items. */
            if (translated != stripped[i] && !strchr(translated, ';'))
                items[i] = translated;
        }
        size += strlen(items[i]) + 1;
    }

    result = G_str_concat(items, count, ";", size);

    for (i = 0; i < count; i++)
        G_free(stripped[i]);
    G_free(stripped);
    G_free(items);
    G_free_tokens(tokens);

    return result;
}
