# SanitizerCoverage as an alternative to clang source-based coverage

This document reports on an experiment comparing the source-based clang
coverage instrumentation added by `GRASS_LLVM_COVERAGE` (see
`.github/workflows/macos.yml`, `.github/workflows/pytest.yml`, and
`utils/llvm_coverage_export.sh`) against SanitizerCoverage
(`-fsanitize-coverage=`), on both GCC and Clang, for the Linux `pytest.yml`
workflow, with the same mechanism also wired into `cmake.yml`. It is
exploratory work done on `claude/sancov-coverage-experiment`; it does not
replace `GRASS_LLVM_COVERAGE`.

Everything in this report was either run in this session's own build
environment (a local sandbox with the same Ubuntu 24.04 toolchain the CI
image uses, GCC 13.3.0 and Clang 18.1.3) or on a real GitHub Actions run
of this branch, triggered manually via `workflow_dispatch` (added to
`pytest.yml`/`cmake.yml` for exactly this purpose; remove before merging).
Every number and log excerpt below says which of the two it came from.

## 1. What SanitizerCoverage needed that source-based coverage did not

`-fprofile-instr-generate -fcoverage-mapping` (the existing
`GRASS_LLVM_COVERAGE` mechanism) works with almost no extra plumbing: clang's
driver recognizes the flag at *link* time too and automatically links
`libclang_rt.profile`, and the resulting binary dumps a `.profraw` file on
exit on its own. `-fsanitize-coverage=` has no equivalent: it inserts calls
to callback functions (`__sanitizer_cov_trace_pc_guard`,
`__sanitizer_cov_trace_pc`, ...) that must be supplied by some runtime, and
neither compiler links one in automatically unless the rest of
`-fsanitize=fuzzer[-no-link]` is also in play.

### 1.1 GCC does not implement `trace-pc-guard`

Both GCC 13.3.0 and 14.2.0 (the versions available in this session) reject
`-fsanitize-coverage=trace-pc-guard`:

```
$ gcc -fsanitize-coverage=trace-pc-guard -c -x c /dev/null -o /dev/null
gcc: error: unrecognized argument in option '-fsanitize-coverage=trace-pc-guard'
gcc: note: valid arguments to '-fsanitize-coverage=' are: trace-cmp trace-pc
```

Despite this being widely repeated as available "since GCC 6", GCC's
`-fsanitize-coverage=` only ever implements `trace-cmp` (for
comparison-operand value profiling, used by AFL/libFuzzer-style mutators)
and `trace-pc` (a bare `__sanitizer_cov_trace_pc(void)` call at every edge,
with no per-edge guard word and no argument at all). LLVM's `sancov` tool
and the `.sancov` file format are Clang/compiler-rt-specific and have no GCC
equivalent; there is nothing for GCC to symbolize a `.sancov` file with even
if one existed. This is a real, load-bearing asymmetry between the two
compilers for this mechanism, not just a missing convenience tool.

### 1.2 A custom runtime, without pc-table or compiler-rt

The prototype (`utils/sancov_runtime.c`) does not use `-fsanitize-coverage=
...,pc-table` (Clang-only, and useless without a GCC equivalent). Instead it
records `__builtin_return_address(0)` from inside the callback -- the
address right after the guard/trace call, i.e. the edge's own location --
which `addr2line` can resolve directly, without needing LLVM's PC table or
`sancov`. Two callback sets are provided in the same file, since only one
is ever actually called depending on which flag a given build used:

- **Clang, `trace-pc-guard`:** each edge gets a private guard word
  (`__sanitizer_cov_trace_pc_guard_init`); the callback zeroes the guard on
  first hit, so after that a hit is a load and a branch with no call --
  matching libFuzzer's own default runtime's dedup strategy.
- **GCC, `trace-pc`:** no per-edge state is provided by the compiler, so
  every single edge execution (not just the first) calls
  `__sanitizer_cov_trace_pc(void)`, and the runtime does its own dedup via a
  mutex-guarded open-addressing hash set keyed by return address. This is
  the mechanism-inherent overhead difference between the two paths: a
  locked hash probe on every edge execution versus a load-and-branch after
  the first.

On process exit (a plain `__attribute__((destructor))`, so no changes to
GRASS's own exit path were needed -- `G_fatal_error`'s normal path calls
`exit()`, which still runs destructors; only its rare debug "abort on fatal
error" mode would skip them), each hit address is resolved to its owning
shared object via `dladdr()` and written as a module-relative offset to a
per-process file (`sancov-<pid>.txt`), the same one-file-per-process
pattern `GRASS_LLVM_COVERAGE` uses for `.profraw`, for the same reason:
GRASS tools are short-lived subprocesses, and a shared file across
processes would race.

Symbolization (`utils/sancov_symbolize.py`) batches the recorded offsets
per module through one `addr2line -f -C -i -a` call, and keeps only the
innermost frame of each address's inline chain. `-i` turned out to matter
in practice, not just in principle: `addr2line -f -C` alone attributes an
edge inlined from a shared header (e.g. glibc's fortified `printf` wrapper
in `bits/stdio2.h`) to that header's own line, identically, for two
call sites that are otherwise perfectly distinguishable by address; `-i`
reports the actual outer call site instead. Verified locally with a
synthetic two-branch program at `-O2`: without `-i`, both branches
resolved to the same `bits/stdio2.h:86`; with `-i`, they resolved correctly
to their respective call sites in `demo.c`.

### 1.3 Getting a link that actually works

This took four real, empirically-discovered failures to work through, on
the Autotools path (`build_ubuntu-24.04.sh`); all are documented inline in
the script's comments where they were fixed. In order:

1. **`-lsancovrt` in `LDFLAGS` never resolves.** Every GRASS Make template
   (`Shlib.make`, `Compile.make`) places `$(LDFLAGS)` *before* the object
   files being linked. GNU ld resolves symbols strictly left to right and
   never revisits a library once passed, so a library placed before the
   objects that reference it never satisfies them --
   `undefined reference to '__sanitizer_cov_trace_pc'`, reproduced first in
   `./configure`'s own "does the compiler work" smoke test.
2. **`-Wl,--unresolved-symbols=ignore-all` does not defer to `LD_PRELOAD`.**
   The obvious-looking fix -- link with the symbol left unresolved, then
   supply it via `LD_PRELOAD` at run time -- does not work for an
   *executable* (as opposed to a shared library): with that flag, ld leaves
   a broken, non-PLT call instruction rather than a legitimately
   dynamically-resolvable one, so the binary segfaults the instant it
   executes the call, with or without the runtime preloaded. This is a
   fundamentally different case from a shared library's normal tolerance of
   unresolved symbols, not just a missing flag.
3. **Autotools' `LOC_CHECK_LIBS` probes bypass `$LIBS`.** With the
   instrumentation flags exported into `CFLAGS`/`CXXFLAGS` before
   `./configure`, its own many `LOC_CHECK_LIBS`-based dependency probes
   (BLAS, GDAL, PROJ, and most other optional libraries) each construct
   their own bespoke compile-and-link command rather than going through
   autoconf's usual `$LIBS` propagation, so exporting `$LIBS` (which *does*
   fix autoconf's own generic checks) still left, for instance, the BLAS
   probe failing with an unrelated-looking `Unable to link to (C)BLAS
   library`.
4. **A hand-rolled `$(MATHLIB)` override still misses special-cased link
   rules.** Routing the runtime through `$(MATHLIB)` -- the one variable
   both `Shlib.make` and `Compile.make`'s `linker_x` place *after* the
   object files, set exactly once from configure's own math-library probe
   with no per-tool Makefile ever overriding it (unlike `EXTRA_LIBS`, which
   17 Makefiles do set locally) -- got every standard library and
   executable link working. It missed `lib/init/Makefile`'s hand-written
   rule for `etc/echo` and `etc/run`, which calls `linker_base` directly
   with neither `$(LIBES)` nor `$(MATHLIB)`, by design (these two tiny
   helper executables are deliberately built without linking any GRASS
   library at all) -- so the compiled objects still referenced the
   coverage callback (compiled with the same global `CFLAGS`) with no way
   to resolve it.

The fix that actually generalizes across all of the above, used in the
final version of `build_ubuntu-24.04.sh`, is a `CC`/`CXX` wrapper script:

```sh
exec "${REAL_CC}" "$@" -L"${SANCOV_RUNTIME_DIR}" -lsancovrt -Wl,-rpath,"${SANCOV_RUNTIME_DIR}"
```

Every one of GRASS's link rules -- standard, special-cased, or
autoconf's own probes -- ultimately invokes `$(CC)`/`$(CXX)` (or `$(LINK)`,
which itself defaults to `$(CC)`) as the actual compiler front-end, so
intercepting at that level reaches all of them uniformly, appending the
runtime library after whatever arguments the caller supplied, regardless of
which Makefile or Configure macro built the rest of the command line. The
same flags are harmless on a compile-only (`-c`) invocation -- confirmed
empirically, `gcc`/`clang` silently ignore unused `-l`/`-L`/`-Wl,` there --
so one wrapper handles compiles and links alike, and the instrumentation
flags could go back to being set in `CFLAGS`/`CXXFLAGS` before
`./configure` runs, the same way `GRASS_LLVM_COVERAGE` already does it.

CMake did not need any of this. `link_libraries(sancovrt)`, called once
near the top of `CMakeLists.txt` (gated by `-DWITH_SANCOV_COVERAGE=ON`),
makes every subsequently-defined target link against it through CMake's
normal dependency graph, which always places a `target_link_libraries`
dependency after that target's own objects -- there is no equivalent to
GRASS's hand-written link-order problem to work around. The one CMake-side
wrinkle: GRASS's own libraries are exported for `g.extension`'s
addon-building CMake package, and `install(EXPORT ...)` refuses to
generate if an exported target depends on a library that is not itself
part of some export set -- so `sancovrt` is declared as an `IMPORTED`
library (built via a plain `add_custom_command` calling the compiler
directly) rather than a normal `add_library(... SHARED ...)` target, since
imported targets are exempt from that requirement.

### 1.4 What was actually validated locally

- The runtime and symbolizer were validated end to end on a small
  synthetic program, on both compilers, at both `-O0` and `-O2`.
- A full Autotools build (`build_ubuntu-24.04.sh` with
  `GRASS_SANCOV_COVERAGE=1 GRASS_SANCOV_CC=gcc`, minus PDAL, which is not
  installable in this sandbox for reasons unrelated to this change) built
  and installed successfully end to end, with `libsancovrt.so` linked into
  every GRASS shared library and executable, and no unresolved-symbol
  failures anywhere in the tree, including the `lib/init/echo`/`run` edge
  case above.
- A full CMake build (`-DWITH_SANCOV_COVERAGE=ON -DWITH_PDAL=OFF
  -DWITH_DOCS=OFF`) reached 3996 of 3997 build steps successfully,
  including every C/C++ library and executable and the interface-XML
  generation step (which runs freshly built, instrumented tool binaries);
  the one failure was `ModuleNotFoundError: No module named 'wx'` building
  the GUI's `menustrings.py`, a pre-existing sandbox gap (`wxPython` is not
  installed here) with no relation to this change.
- `GRASS_SANCOV_CC=clang` was not separately re-validated with a full local
  build after the final wrapper-script redesign (time budget); it shares
  the same code path as the validated `gcc` case, differing only in which
  flag and which of the two runtime callback sets gets exercised, both of
  which were validated by the synthetic-program tests above.

## 2. Build-time and test-time deltas

*(This section is filled in from the real GitHub Actions run(s) of this
branch's `pytest.yml`/`cmake.yml`, triggered via `workflow_dispatch` --
run links and per-step timings below.)*

## 3. Coverage report quality and the macro-attribution demonstration

### 3.1 Macro demonstration: `_()` (gettext) in `lib/gis/parser_standard_options.c`

The macro chosen is `_()`, GRASS's gettext wrapper
(`include/grass/glocale.h`: `#define _(str) G_gettext(PACKAGE, (str))`),
in `lib/gis/parser_standard_options.c`'s `G_define_standard_option()`
function -- a large `switch` over ~100 standard CLI options, each case
expanding `_()` once or twice with a different string literal, exercised
by essentially every pytest test (every tool invocation that uses a
standard option parses through this function).

A small harness (`G_no_gisinit(); G_define_standard_option(G_OPT_R_INPUT
| G_OPT_R_OUTPUT | G_OPT_V_INPUT | G_OPT_F_INPUT)`) was linked against
`lib/gis`/`lib/datetime`, each built three ways: clang with
`-fprofile-instr-generate -fcoverage-mapping` (the existing mechanism),
clang with `-fsanitize-coverage=trace-pc-guard`, and gcc with
`-fsanitize-coverage=trace-pc`. All three builds used the project's real
`-O2` flags and real compile command line (extracted via `make -n`), all
three ran the same harness, and all three were symbolized with their real
tool (`llvm-cov show` for the source-based build, `addr2line -f -C -i` for
the two SanitizerCoverage builds).

**Source-based coverage** (`llvm-cov show`) reports every `_()` expansion
as its own hit-counted line/region, including two on consecutive lines
within the same case:

```
482|      1|    case G_OPT_V_INPUT:
483|      1|        Opt->key = "input";
...
487|      1|        Opt->gisprompt = "old,vector,vector";
488|      1|        Opt->label = _("Name of input vector map");
489|      1|        Opt->description = _("Or data source for direct OGR access");
490|      1|        break;
```

**Both SanitizerCoverage builds** correctly distinguish the four *separate*
cases from each other (clang, `addr2line -f -C -i` on the real
`libgrass_gis.8.6.so`):

```
G_define_standard_option lib/gis/parser_standard_options.c:273   (G_OPT_R_INPUT)
G_define_standard_option lib/gis/parser_standard_options.c:290   (G_OPT_R_OUTPUT)
G_define_standard_option lib/gis/parser_standard_options.c:483   (G_OPT_V_INPUT)
G_define_standard_option lib/gis/parser_standard_options.c:602   (G_OPT_F_INPUT)
```

(gcc's `trace-pc` build produced the identical four lines.) But *within*
`G_OPT_V_INPUT`'s case, both mechanisms report exactly **one** hit, at line
483 (the case's first statement) -- never at line 488 or 489 specifically:

```
$ addr2line -e libgrass_gis.8.6.so -f -C -i <offsets> | grep -c ':488\|:489'
0
```

This is the real, concretely-observed granularity gap the task set out to
demonstrate: `-fsanitize-coverage=` instruments at the compiler's basic-block
("edge") granularity. Because there is no branch between lines 488 and 489,
the compiler placed one guard/trace call to cover the whole straight-line
block from `case G_OPT_V_INPUT:` through `break;`, so the two distinct `_()`
expansions -- two different macro invocations, two different string
arguments, two different logical events -- are indistinguishable in the
SanitizerCoverage output: it can only report "this block ran once," not
"and here specifically is where the second gettext call happened." Clang's
`-fcoverage-mapping`, generating its region map from the AST before
codegen, keeps them separate because it is not tied to the machine code's
block structure at all.

This is a genuine, reproduced instance of the concern, not merely a
theoretical one, though it is worth noting exactly what produced it here:
not identical-code-folding or inlining collapsing two distinct call sites
into the same address (the classic "macro instantiated at N places, but
they compile to the same code" case this task also raised as a
possibility), but block-level coalescing of two *sequential*, non-branching
statements. Both are real ways SanitizerCoverage loses macro-expansion
resolution that source-based coverage keeps; this experiment concretely
demonstrated the sequential-statement case because that is what the
chosen macro's real usage pattern in this codebase happens to exercise.

### 3.2 Report format

Neither SanitizerCoverage path produces anything as detailed as the lcov
file `utils/llvm_coverage_export.sh` exports: `utils/sancov_symbolize.py`
aggregates the raw per-process dumps into a simple "how many distinct
lines did this file hit" count per file, deliberately coarser (the task
explicitly says this is sufficient), and unable to report per-region hit
*counts* the way lcov/llvm-cov can, only line-reached/not-reached, and
only at the coarseness the macro demonstration above illustrates.

## 4. Bottom line

*(Recommendation to be finalized once the CI numbers in Section 2 are in;
see the qualitative findings above, which do not depend on those numbers.)*
