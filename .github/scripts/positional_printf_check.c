/* Throwaway check: do POSIX positional printf arguments work here?
 * Results are printed as PASS/FAIL lines; the exit status is always 0. */
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#define BUFSZ 128

static void report(const char *func, const char *fmt, const char *result,
                   const char *expected)
{
    printf("%s: func=%s format=\"%s\" result=\"%s\" expected=\"%s\"\n",
           strcmp(result, expected) == 0 ? "PASS" : "FAIL", func, fmt, result,
           expected);
}

/* Mimics G_vasprintf(): formats through vsnprintf with a va_list. */
static int wrap_vsnprintf(char *buf, size_t n, const char *fmt, ...)
{
    va_list ap;
    int ret;

    va_start(ap, fmt);
    ret = vsnprintf(buf, n, fmt, ap);
    va_end(ap);
    return ret;
}

#ifdef _MSC_VER
static int wrap_vsprintf_p(char *buf, size_t n, const char *fmt, ...)
{
    va_list ap;
    int ret;

    va_start(ap, fmt);
    ret = _vsprintf_p(buf, n, fmt, ap);
    va_end(ap);
    return ret;
}
#endif

int main(void)
{
    char buf[BUFSZ];
    const char *fmt_s = "%2$s %1$s";
    const char *fmt_m = "%2$d %1$s";

#ifdef _MSC_VER
    printf("compiler: MSVC _MSC_VER=%d\n", _MSC_VER);
#endif
#ifdef __GNUC__
    printf("compiler: GCC %d.%d\n", __GNUC__, __GNUC_MINOR__);
#endif
#ifdef _UCRT
    printf("runtime: _UCRT defined\n");
#else
    printf("runtime: _UCRT not defined\n");
#endif
#ifdef __USE_MINGW_ANSI_STDIO
    printf("__USE_MINGW_ANSI_STDIO=%d\n", __USE_MINGW_ANSI_STDIO);
#else
    printf("__USE_MINGW_ANSI_STDIO not defined\n");
#endif

    memset(buf, 0, sizeof buf);
    snprintf(buf, sizeof buf, fmt_s, "a", "b");
    report("snprintf", fmt_s, buf, "b a");

    memset(buf, 0, sizeof buf);
    snprintf(buf, sizeof buf, fmt_m, "x", 42);
    report("snprintf", fmt_m, buf, "42 x");

    memset(buf, 0, sizeof buf);
    wrap_vsnprintf(buf, sizeof buf, fmt_s, "a", "b");
    report("vsnprintf(wrapper)", fmt_s, buf, "b a");

    memset(buf, 0, sizeof buf);
    wrap_vsnprintf(buf, sizeof buf, fmt_m, "x", 42);
    report("vsnprintf(wrapper)", fmt_m, buf, "42 x");

#ifdef _MSC_VER
    memset(buf, 0, sizeof buf);
    _sprintf_p(buf, sizeof buf, fmt_s, "a", "b");
    report("_sprintf_p", fmt_s, buf, "b a");

    memset(buf, 0, sizeof buf);
    _sprintf_p(buf, sizeof buf, fmt_m, "x", 42);
    report("_sprintf_p", fmt_m, buf, "42 x");

    memset(buf, 0, sizeof buf);
    wrap_vsprintf_p(buf, sizeof buf, fmt_s, "a", "b");
    report("_vsprintf_p(wrapper)", fmt_s, buf, "b a");

    memset(buf, 0, sizeof buf);
    wrap_vsprintf_p(buf, sizeof buf, fmt_m, "x", 42);
    report("_vsprintf_p(wrapper)", fmt_m, buf, "42 x");
#endif

    return 0;
}
