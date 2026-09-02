/* Minimal SanitizerCoverage runtime for GRASS's opt-in GRASS_SANCOV_COVERAGE
 * build (see build_ubuntu-24.04.sh and doc/development/
 * sancov_coverage_experiment.md). Compiled once into a small shared
 * library and linked into every GRASS binary via LDFLAGS, so it does not
 * depend on -fsanitize=fuzzer[-no-link] or any compiler-rt component.
 *
 * -fsanitize-coverage= supports two different edge-instrumentation ABIs
 * depending on the compiler and chosen sub-option, so this file provides
 * both callback sets; whichever one is unused by a given build is simply
 * never called.
 *
 * Clang, -fsanitize-coverage=trace-pc-guard: the compiler gives each edge
 * a private guard word (via __sanitizer_cov_trace_pc_guard_init) and
 * calls __sanitizer_cov_trace_pc_guard(&guard) on every execution. This
 * runtime dedups by zeroing the guard on first hit, so after that the
 * compiler-emitted check is a load and a branch with no call -- the same
 * strategy libFuzzer's own runtime uses to keep steady-state overhead
 * low.
 *
 * GCC, -fsanitize-coverage=trace-pc: GCC 13/14 do not implement
 * trace-pc-guard (confirmed empirically; only trace-cmp and trace-pc are
 * accepted). trace-pc calls __sanitizer_cov_trace_pc(void) with no
 * per-edge state at all, so this runtime does its own dedup via a
 * mutex-guarded hash set keyed by return address -- a hash probe on every
 * single edge execution, not just the first, which is the mechanism-
 * inherent overhead difference from the guard-based path.
 *
 * Neither path uses -fsanitize-coverage=pc-table (GCC has no equivalent,
 * and Clang's needs the -fsanitize=fuzzer[-no-link] runtime to consume
 * it). Instead each callback records __builtin_return_address(0): the
 * address right after the guard/trace call, i.e. the edge location
 * itself, which a symbolizer can resolve directly with addr2line -- see
 * utils/sancov_symbolize.py.
 *
 * On process exit (a destructor, so no changes to GRASS's own exit path
 * are needed), each hit address is resolved to its containing shared
 * object via dladdr() and written as a module-relative offset to a
 * per-process dump file, mirroring the profraw-per-process pattern the
 * existing GRASS_LLVM_COVERAGE path uses for the same reason: GRASS tools
 * are short-lived subprocesses, one dump file per process avoids
 * cross-process write collisions. A destructor is not reached if a
 * process is killed by a signal or calls abort() (e.g. GRASS's debug
 * "abort on fatal error" mode); the normal G_fatal_error exit() path is
 * unaffected since destructors run for exit().
 */

#define _GNU_SOURCE
#include <dlfcn.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define MAX_GUARD_HITS 4000000
static void *guard_hits[MAX_GUARD_HITS];
static _Atomic uint32_t n_guard_hits;

void __sanitizer_cov_trace_pc_guard_init(uint32_t *start, uint32_t *stop)
{
    static uint32_t n;

    if (start == stop || *start)
        return;
    for (uint32_t *x = start; x < stop; x++)
        *x = ++n;
}

void __sanitizer_cov_trace_pc_guard(uint32_t *guard)
{
    if (!*guard)
        return;
    *guard = 0;

    uint32_t i = n_guard_hits++;

    if (i < MAX_GUARD_HITS)
        guard_hits[i] = __builtin_return_address(0);
}

#define TRACE_PC_TABLE_BITS 21
#define TRACE_PC_TABLE_SIZE (1u << TRACE_PC_TABLE_BITS)
static void *trace_pc_table[TRACE_PC_TABLE_SIZE];
static pthread_mutex_t trace_pc_lock = PTHREAD_MUTEX_INITIALIZER;

void __sanitizer_cov_trace_pc(void)
{
    void *pc = __builtin_return_address(0);

    pthread_mutex_lock(&trace_pc_lock);
    uintptr_t h = ((uintptr_t)pc >> 4) & (TRACE_PC_TABLE_SIZE - 1);

    for (unsigned probe = 0; probe < TRACE_PC_TABLE_SIZE; probe++) {
        uintptr_t idx = (h + probe) & (TRACE_PC_TABLE_SIZE - 1);

        if (trace_pc_table[idx] == pc)
            break;
        if (trace_pc_table[idx] == NULL) {
            trace_pc_table[idx] = pc;
            break;
        }
    }
    pthread_mutex_unlock(&trace_pc_lock);
}

static void write_hit(FILE *f, void *pc)
{
    Dl_info info;

    if (dladdr(pc, &info) && info.dli_fname) {
        uintptr_t off = (uintptr_t)pc - (uintptr_t)info.dli_fbase;

        fprintf(f, "%s %lx\n", info.dli_fname, (unsigned long)off);
    }
}

__attribute__((destructor)) static void sancov_dump(void)
{
    const char *dir = getenv("GRASS_SANCOV_DUMP_DIR");

    if (!dir)
        return;

    char path[4096];

    snprintf(path, sizeof(path), "%s/sancov-%d.txt", dir, getpid());
    FILE *f = fopen(path, "w");

    if (!f)
        return;

    uint32_t n = n_guard_hits;

    if (n > MAX_GUARD_HITS)
        n = MAX_GUARD_HITS;
    for (uint32_t i = 0; i < n; i++)
        write_hit(f, guard_hits[i]);

    for (uint32_t i = 0; i < TRACE_PC_TABLE_SIZE; i++)
        if (trace_pc_table[i])
            write_hit(f, trace_pc_table[i]);

    fclose(f);
}
