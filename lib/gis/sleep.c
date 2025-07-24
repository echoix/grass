#include <grass/config.h>
#ifndef _WIN32
#include <unistd.h>
#endif
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif // !NOMINMAX
#define WIN32_LEAN_AND_MEAN
#define VC_EXTRALEAN
#include <windows.h>
#undef NOMINMAX
#undef WIN32_LEAN_AND_MEAN
#undef VC_EXTRALEAN
#endif
#include <grass/gis.h>

/* Sleep */
void G_sleep(unsigned int seconds)
{
#ifdef _WIN32
    /* note: Sleep() cannot be interrupted */
    Sleep((seconds) * 1000);
#else
    sleep(seconds);
#endif
}
