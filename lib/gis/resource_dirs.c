/*!
   \file lib/gis/resource_dirs.c

   \brief GIS Library - Get paths to resource directories.

   \author Nicklas Larsson

   (c) 2025 by the GRASS Development Team

   SPDX-License-Identifier: GPL-2.0-or-later
 */

#include <stdio.h>
#include <stdlib.h>

#include <grass/gis.h>
#include <grass/glocale.h>

#include "resource_dirs.h"

static const char *get_g_env(const char *, const char *, int *, char **);

const char *G_colors_dir(void)
{
    static int initialized;
    static char *fallback;

    return get_g_env("GRASS_COLORSDIR", GRASS_COLORSDIR_REL, &initialized,
                     &fallback);
}

const char *G_etcbin_dir(void)
{
    static int initialized;
    static char *fallback;

    return get_g_env("GRASS_ETCBINDIR", GRASS_ETCBINDIR_REL, &initialized,
                     &fallback);
}

const char *G_etc_dir(void)
{
    static int initialized;
    static char *fallback;

    return get_g_env("GRASS_ETCDIR", GRASS_ETCDIR_REL, &initialized, &fallback);
}

const char *G_fonts_dir(void)
{
    static int initialized;
    static char *fallback;

    return get_g_env("GRASS_FONTSDIR", GRASS_FONTSDIR_REL, &initialized,
                     &fallback);
}

const char *G_locale_dir(void)
{
    static int initialized;
    static char *fallback;

    return get_g_env("GRASS_LOCALEDIR", GRASS_LOCALEDIR_REL, &initialized,
                     &fallback);
}

/* Return the value of env_var. If it is not set, e.g., when a tool is run
   directly by a program which sets only GISBASE, return GISBASE/rel_path,
   built on the first call and kept in *fallback. */
static const char *get_g_env(const char *env_var, const char *rel_path,
                             int *initialized, char **fallback)
{
    const char *value = getenv(env_var);
    if (value && *value)
        return value;

    /* Not using G_gisbase(): its G_getenv() would fail with a message about
       GISBASE rather than about env_var. */
    const char *gisbase = getenv("GISBASE");
    if (!gisbase || !*gisbase)
        G_fatal_error(_("Incomplete GRASS session: Variable '%s' not set"),
                      env_var);

    if (!G_is_initialized(initialized)) {
        char path[GPATH_MAX];

        snprintf(path, sizeof(path), "%s/%s", gisbase, rel_path);
        *fallback = G_store(path);
        G_initialize_done(initialized);
    }

    return *fallback;
}
