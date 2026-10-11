/*!
   \file lib/gis/units.c

   \brief GIS Library - Units management and conversion

   SPDX-FileCopyrightText: 2001-2010 GRASS Development Team
   SPDX-License-Identifier: GPL-2.0-or-later

   \author Original author CERL
   \author Adopted for libgis by Martin Landa <landa.martin gmail.com> (2010)
   \author Temporal units and unit type check from Soeren gebbert <soerengebbert
   googlemail.com> (2012)
 */

#include <string.h>

#include <grass/gis.h>
#include <grass/glocale.h>

/*!
   \brief Units conversion from meters to units

   Units codes (gis.h):
   - U_METERS
   - U_KILOMETERS
   - U_MILES
   - U_FEET
   - U_USFEET

   Returns a factor which converts meters to units (by multiplication).

   \param units units code

   \return factor
 */
double G_meters_to_units_factor(int units)
{
    switch (units) {
    case U_METERS:
        return 1.0;
        break;

    case U_KILOMETERS:
        return 1.0e-3;
        break;

    case U_MILES:
        return 6.21371192237334e-4; /*  1 / (0.0254 * 12 * 5280)    */
        break;

    case U_FEET:
        return 3.28083989501312; /*  1 / (0.0254 * 12)    */
        break;

    case U_USFEET:
        return 3.28083333333333; /*  1 / (1200/3937)    */
        break;

    default:
        return 1.0;
        break;
    }

    return 1.0;
}

/*!
   \brief Units conversion from square meters to square units

   Units codes (gis.h):
   - U_METERS
   - U_KILOMETERS
   - U_ACRES
   - U_HECTARES
   - U_MILES
   - U_FEET
   - U_USFEET

   Returns a factor which converts square meters to square units (by
   multiplication).

   \param units units code

   \return factor
 */
double G_meters_to_units_factor_sq(int units)
{
    switch (units) {
    case U_METERS:
        return 1.0;
        break;

    case U_KILOMETERS:
        return 1.0e-6;
        break;

    case U_ACRES:
        return 2.47105381467165e-4; /* 640 acres in a sq mile */
        break;

    case U_HECTARES:
        return 1.0e-4;
        break;

    case U_MILES:
        return 3.86102158542446e-7; /*  1 / (0.0254 * 12 * 5280)^2  */
        break;

    case U_FEET:
        return 10.7639104167097; /*  1 / (0.0254 * 12)^2  */
        break;

    case U_USFEET:
        return 10.7638673611111; /*  1 / (1200/3937)^2    */
        break;

    default:
        return 1.0;
        break;
    }

    return 1.0;
}

/** \brief Check if the unit is of spatial type

  \param units units code from gis.h

  \return 1 if True, 0 otherwise
 */
int G_is_units_type_spatial(int units)
{
    switch (units) {
    case U_METERS:
        return 1;
    case U_KILOMETERS:
        return 1;
    case U_HECTARES:
        return 1;
    case U_ACRES:
        return 1;
    case U_MILES:
        return 1;
    case U_FEET:
        return 1;
    case U_USFEET:
        return 1;
    case U_RADIANS:
        return 1;
    case U_DEGREES:
        return 1;
    }
    return 0;
}

/** \brief Check if the unit is of temporal type

  \param units units code from gis.h

  \return 1 if True, 0 otherwise
 */
int G_is_units_type_temporal(int units)
{
    switch (units) {
    case U_YEARS:
        return 1;
    case U_MONTHS:
        return 1;
    case U_DAYS:
        return 1;
    case U_HOURS:
        return 1;
    case U_MINUTES:
        return 1;
    case U_SECONDS:
        return 1;
    }
    return 0;
}

static const char *units_name(int units, int plural, int square, int localize)
{
    switch (units) {
    case U_UNKNOWN:
        if (square)
            return plural
                       // GTC: localized area units
                       ? (localize ? _("square units") : "square units")
                       // GTC: localized area units
                       : (localize ? _("square unit") : "square unit");
        else
            return plural
                       // GTC: localized units
                       ? (localize ? _("units") : "units")
                       // GTC: localized units
                       : (localize ? _("unit") : "unit");
        break;

    case U_METERS:
        if (square)
            return plural
                       // GTC: localized area units
                       ? (localize ? _("square meters") : "square meters")
                       // GTC: localized area units
                       : (localize ? _("square meter") : "square meter");
        else
            return plural
                       // GTC: localized units
                       ? (localize ? _("meters") : "meters")
                       // GTC: localized units
                       : (localize ? _("meter") : "meter");
        break;

    case U_KILOMETERS:
        if (square)
            return plural
                       // GTC: localized area units
                       ? (localize ? _("square kilometers") : "square kilometers")
                       // GTC: localized area units
                       : (localize ? _("square kilometer") : "square kilometer");
        else
            return plural
                       // GTC: localized units
                       ? (localize ? _("kilometers") : "kilometers")
                       // GTC: localized units
                       : (localize ? _("kilometer") : "kilometer");
        break;

    case U_ACRES:
        if (square)
            return plural
                       // GTC: localized area units
                       ? (localize ? _("acres") : "acres")
                       // GTC: localized area units
                       : (localize ? _("acre") : "acre");
        else
            return units_name(G_database_unit(), plural, square, localize);
        break;

    case U_HECTARES:
        if (square)
            return plural
                       // GTC: localized area units
                       ? (localize ? _("hectares") : "hectares")
                       // GTC: localized area units
                       : (localize ? _("hectare") : "hectare");
        else
            return units_name(G_database_unit(), plural, square, localize);
        break;

    case U_MILES:
        if (square)
            return plural
                       // GTC: localized area units
                       ? (localize ? _("square miles") : "square miles")
                       // GTC: localized area units
                       : (localize ? _("square mile") : "square mile");
        else
            return plural
                       // GTC: localized units
                       ? (localize ? _("miles") : "miles")
                       // GTC: localized units
                       : (localize ? _("mile") : "mile");
        break;

    case U_FEET:
        if (square)
            return plural
                       // GTC: localized area units, do not confuse with US feet
                       ? (localize ? _("square feet") : "square feet")
                       // GTC: localized area units, do not confuse with US foot
                       : (localize ? _("square foot") : "square foot");
        else
            return plural
                       // GTC: localized units, do not confuse with US feet
                       ? (localize ? _("feet") : "feet")
                       // GTC: localized units, do not confuse with US foot
                       : (localize ? _("foot") : "foot");
        break;

    case U_USFEET:
        if (square)
            return plural
                       // GTC: localized area units, do not confuse with feet
                       ? (localize ? _("square US feet") : "square US feet")
                       // GTC: localized area units, do not confuse with foot
                       : (localize ? _("square US foot") : "square US foot");
        else
            return plural
                       // GTC: localized units, do not confuse with feet
                       ? (localize ? _("US feet") : "US feet")
                       // GTC: localized units, do not confuse with foot
                       : (localize ? _("US foot") : "US foot");
        break;

    case U_DEGREES:
        if (square)
            return plural
                       // GTC: localized area units
                       ? (localize ? _("square degrees") : "square degrees")
                       // GTC: localized area units
                       : (localize ? _("square degree") : "square degree");
        else
            return plural
                       // GTC: localized units
                       ? (localize ? _("degrees") : "degrees")
                       // GTC: localized units
                       : (localize ? _("degree") : "degree");
        break;

    case U_YEARS:
        return plural
                   // GTC: localized time units
                   ? (localize ? _("years") : "years")
                   // GTC: localized time units
                   : (localize ? _("year") : "year");
        break;

    case U_MONTHS:
        return plural
                   // GTC: localized time units
                   ? (localize ? _("months") : "months")
                   // GTC: localized time units
                   : (localize ? _("month") : "month");
        break;

    case U_DAYS:
        return plural
                   // GTC: localized time units
                   ? (localize ? _("days") : "days")
                   // GTC: localized time units
                   : (localize ? _("day") : "day");
        break;

    case U_HOURS:
        return plural
                   // GTC: localized time units
                   ? (localize ? _("hours") : "hours")
                   // GTC: localized time units
                   : (localize ? _("hour") : "hour");
        break;

    case U_MINUTES:
        return plural
                   // GTC: localized time units
                   ? (localize ? _("minutes") : "minutes")
                   // GTC: localized time units
                   : (localize ? _("minute") : "minute");
        break;

    case U_SECONDS:
        return plural
                   // GTC: localized time units
                   ? (localize ? _("seconds") : "seconds")
                   // GTC: localized time units
                   : (localize ? _("second") : "second");
        break;
    }

    return NULL;
}

/*!
   \brief Get localized units name

   Units codes (gis.h):
   - U_METERS
   - U_KILOMETERS
   - U_ACRES
   - U_HECTARES
   - U_MILES
   - U_FEET
   - U_USFEET

   The name is translated, so it is meant for messages and other text for
   people. Use G_get_units_name_untranslated() for machine-readable output.

   \param units units code
   \param plural plural form if true
   \param square area units if true

   \return units name
   \return NULL if units not found
 */
const char *G_get_units_name(int units, int plural, int square)
{
    return units_name(units, plural, square, 1);
}

/*!
   \brief Get units name in English, independent of the locale

   Same as G_get_units_name(), but never translated, so the result is suitable
   for machine-readable output (JSON, shell style) and for comparison with
   names which G_units() recognizes.

   \param units units code
   \param plural plural form if true
   \param square area units if true

   \return units name
   \return NULL if units not found
 */
const char *G_get_units_name_untranslated(int units, int plural, int square)
{
    return units_name(units, plural, square, 0);
}

/*!
   \brief Get units code by name

   Units codes (gis.h):
   - U_METERS
   - U_KILOMETERS
   - U_ACRES
   - U_HECTARES
   - U_MILES
   - U_FEET
   - U_USFEET
   - ...
   - U_YEARS
   - ...

   \param units_name units name (singular or plural form)

   \return units code
   \return U_UNKNOWN if not found
 */
int G_units(const char *units_name)
{
    if (units_name == NULL) {
        return G_database_unit();
    }

    if (strcasecmp(units_name, "meter") == 0 ||
        strcasecmp(units_name, "meters") == 0)
        return U_METERS;
    else if (strcasecmp(units_name, "kilometer") == 0 ||
             strcasecmp(units_name, "kilometers") == 0)
        return U_KILOMETERS;
    else if (strcasecmp(units_name, "acre") == 0 ||
             strcasecmp(units_name, "acres") == 0)
        return U_ACRES;
    else if (strcasecmp(units_name, "hectare") == 0 ||
             strcasecmp(units_name, "hectares") == 0)
        return U_HECTARES;
    else if (strcasecmp(units_name, "mile") == 0 ||
             strcasecmp(units_name, "miles") == 0)
        return U_MILES;
    else if (strcasecmp(units_name, "foot") == 0 ||
             strcasecmp(units_name, "feet") == 0)
        return U_FEET;
    else if (strcasecmp(units_name, "foot_us") == 0 ||
             strcasecmp(units_name, "foot_uss") == 0)
        return U_USFEET;
    else if (strcasecmp(units_name, "degree") == 0 ||
             strcasecmp(units_name, "degrees") == 0)
        return U_DEGREES;
    else if (strcasecmp(units_name, "year") == 0 ||
             strcasecmp(units_name, "years") == 0)
        return U_YEARS;
    else if (strcasecmp(units_name, "month") == 0 ||
             strcasecmp(units_name, "months") == 0)
        return U_MONTHS;
    else if (strcasecmp(units_name, "day") == 0 ||
             strcasecmp(units_name, "days") == 0)
        return U_DAYS;
    else if (strcasecmp(units_name, "hour") == 0 ||
             strcasecmp(units_name, "hours") == 0)
        return U_HOURS;
    else if (strcasecmp(units_name, "minute") == 0 ||
             strcasecmp(units_name, "minutes") == 0)
        return U_MINUTES;
    else if (strcasecmp(units_name, "second") == 0 ||
             strcasecmp(units_name, "seconds") == 0)
        return U_SECONDS;

    return U_UNKNOWN;
}
