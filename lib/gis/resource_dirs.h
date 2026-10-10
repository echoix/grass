/*!
   \file lib/gis/resource_dirs.h

   \brief GIS Library - Default resource directories relative to GISBASE.

   SPDX-FileCopyrightText: GRASS Development Team
   SPDX-License-Identifier: GPL-2.0-or-later
 */

#ifndef GRASS_LIB_GIS_RESOURCE_DIRS_H
#define GRASS_LIB_GIS_RESOURCE_DIRS_H

/* Paths relative to GISBASE, used when the corresponding GRASS_*DIR variable
   is not set. CMake defines them from the install layout; the defaults are
   the legacy layout, which is the only one the Autotools build produces. */
#ifndef GRASS_COLORSDIR_REL
#define GRASS_COLORSDIR_REL "etc/colors"
#endif
#ifndef GRASS_ETCBINDIR_REL
#define GRASS_ETCBINDIR_REL "etc"
#endif
#ifndef GRASS_ETCDIR_REL
#define GRASS_ETCDIR_REL "etc"
#endif
#ifndef GRASS_FONTSDIR_REL
#define GRASS_FONTSDIR_REL "fonts"
#endif
#ifndef GRASS_LOCALEDIR_REL
#define GRASS_LOCALEDIR_REL "locale"
#endif

#endif
