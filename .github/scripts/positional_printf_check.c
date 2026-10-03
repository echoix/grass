/* Throwaway check: do POSIX positional printf arguments work here?
 * Results are printed as PASS/FAIL lines; the exit status is always 0.
 *
 * Optional defines:
 *   USE_LIBINTL            include <libintl.h> first and report its redirects
 *   TEST_LIBINTL_DIRECT    also call libintl_snprintf()/libintl_vsnprintf()
 */
#ifdef USE_LIBINTL
#include <libintl.h>
#endif
#include <inttypes.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define BUFSZ 128

#ifdef TEST_LIBINTL_DIRECT
/* Declared here in case libintl.h only declares them conditionally. */
extern int libintl_snprintf(char *, size_t, const char *, ...);
extern int libintl_vsnprintf(char *, size_t, const char *, va_list);
#endif

static void report(const char *func, const char *fmt, const char *result,
                   const char *expected)
{
    printf("%s: func=%s format=\"%s\" result=\"%s\" expected=\"%s\"\n",
           strcmp(result, expected) == 0 ? "PASS" : "FAIL", func, fmt, result,
           expected);
}

/* Mimics G_vasprintf(): formats through a va_list function. */
#define DEFINE_WRAPPER(name, vfunc)                                       \
    static int name(char *buf, size_t n, const char *fmt, ...)            \
    {                                                                     \
        va_list ap;                                                       \
        int ret;                                                          \
                                                                          \
        va_start(ap, fmt);                                                \
        ret = vfunc(buf, n, fmt, ap);                                     \
        va_end(ap);                                                       \
        return ret;                                                       \
    }

DEFINE_WRAPPER(wrap_vsnprintf, vsnprintf)
#ifdef TEST_LIBINTL_DIRECT
DEFINE_WRAPPER(wrap_libintl_vsnprintf, libintl_vsnprintf)
#endif
#ifdef _MSC_VER
DEFINE_WRAPPER(wrap_vsprintf_p, _vsprintf_p)
#endif

/* Runs all formats through fn(buf, size, fmt, args...). */
#define RUN_CASES(label, fn)                                                 \
    do {                                                                     \
        memset(buf, 0, sizeof buf);                                          \
        fn(buf, sizeof buf, "%2$s %1$s", "a", "b");                          \
        report(label, "%2$s %1$s", buf, "b a");                              \
        memset(buf, 0, sizeof buf);                                          \
        fn(buf, sizeof buf, "%2$d %1$s", "x", 42);                           \
        report(label, "%2$d %1$s", buf, "42 x");                             \
        memset(buf, 0, sizeof buf);                                          \
        fn(buf, sizeof buf, "%2$lu %1$llu", 5ULL, 7UL);                      \
        report(label, "%2$lu %1$llu", buf, "7 5");                           \
        memset(buf, 0, sizeof buf);                                          \
        fn(buf, sizeof buf, "%2$" PRIu64 " %1$s", "x", (uint64_t)123);       \
        report(label, "%2$" PRIu64 " %1$s", buf, "123 x");                   \
    } while (0)

int main(void)
{
    char buf[BUFSZ];

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
#ifdef USE_LIBINTL
    printf("libintl.h included first\n");
#ifdef snprintf
    printf("snprintf IS a macro after libintl.h\n");
#else
    printf("snprintf is NOT a macro after libintl.h\n");
#endif
#ifdef vsnprintf
    printf("vsnprintf IS a macro after libintl.h\n");
#else
    printf("vsnprintf is NOT a macro after libintl.h\n");
#endif
#ifdef _INTL_REDIRECT_MACROS
    printf("_INTL_REDIRECT_MACROS is defined\n");
#else
    printf("_INTL_REDIRECT_MACROS is not defined\n");
#endif
#ifdef _INTL_NO_REDIRECT_PRINTF
    printf("_INTL_NO_REDIRECT_PRINTF is defined\n");
#else
    printf("_INTL_NO_REDIRECT_PRINTF is not defined\n");
#endif
#endif

    RUN_CASES("snprintf", snprintf);
    RUN_CASES("vsnprintf(wrapper)", wrap_vsnprintf);

#ifdef TEST_LIBINTL_DIRECT
    RUN_CASES("libintl_snprintf", libintl_snprintf);
    RUN_CASES("libintl_vsnprintf(wrapper)", wrap_libintl_vsnprintf);
#endif

#ifdef _MSC_VER
    RUN_CASES("_sprintf_p", _sprintf_p);
    RUN_CASES("_vsprintf_p(wrapper)", wrap_vsprintf_p);
#endif

    return 0;
}
