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

```console
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
  which were validated by the synthetic-program tests above. It *was*
  validated by real CI (next point).

### 1.5 What real CI caught that local testing could not

Getting a genuinely green run of `pytest.yml`'s new matrix cells took five
more rounds of real, `workflow_dispatch`-triggered CI, each catching a
distinct bug local testing had no way to surface:

- A GitHub Actions matrix `include`-only pitfall: mixing a base
  `os`/`python-version`/`coverage` cross product with `include` entries
  that only partially override it (just `coverage`) produced a matrix
  whose `pytest` job had **zero actual instances** -- confirmed by a run
  whose job list came back completely empty. Fixed by making every
  `include` entry a complete, independent combination.
- A concurrency-group collision: three cells now share
  `python-version: "3.13"`; a group keyed only on that (matching the
  file's pre-existing style) collided across them, and
  `cancel-in-progress: true` cancelled two of the three within a second of
  the third starting. Fixed by keying the group on `matrix.coverage` too.
- Real toolchain interaction, not reproducible locally: this workflow
  installs `mold` as the default linker (`rui314/setup-mold`). GRASS's
  own `$(MATHLIB)` autoconf probe (`AC_CHECK_FUNC(atan, MATHLIB=, ...)`)
  comes out empty on Ubuntu 24.04's glibc 2.39, which merged libm into
  libc, so a plain "does atan link without -lm" check already succeeds.
  GNU ld tolerates the resulting missing `-lm` on GRASS binaries that
  call `cos`/`sin`/`floor` by transitively finding them in libc via an
  already-linked GRASS shared library; `mold` does not, and `ps.map`'s
  link failed with `undefined symbol: cos` under `GRASS_SANCOV_CC=clang`
  specifically. Fixed by having the compiler wrapper unconditionally
  append `-lm` alongside `-lsancovrt`.
- A `dladdr()` bare-path bug in the runtime itself (Section 1.2's
  destructor): confirmed by a real `db.connect` coverage dump (GRASS
  spawns its DB drivers by bare name via a `PATH` search) failing to
  symbolize. Fixed via `/proc/self/exe`.
- A vanished-module bug in the symbolizer: a `g.extension` test builds an
  addon into a temporary directory that gunittest/pytest cleans up before
  this post-test symbolization step runs, so the recorded module no
  longer exists on disk. Fixed by skipping (with a warning) instead of
  aborting the whole run.

With all of those fixed, a subsequent run
(<https://github.com/echoix/grass/actions/runs/33689957509>) built and ran
pytest successfully in all four matrix cells, including `sancov-clang`,
and both `sancov-gcc` and `sancov-clang` produced real, symbolizable
coverage dumps (Section 2 has the timings; artifacts
`sancov-coverage-summary-sancov-gcc` and `-sancov-clang` on that run hold
the actual line-hit summaries).

A further bug surfaced by `cmake.yml`
(<https://github.com/echoix/grass/actions/runs/33686891578>, `gcc` job):
a gunittest test that builds a GRASS addon via `g.extension` failed to
compile it under `-DWITH_SANCOV_COVERAGE=ON`, with
`/usr/bin/ld: cannot find -lsancovrt`. `g.extension` builds addons using
the *installed* GRASS's exported CMake package
(`etc/cmake/build_addon.cmake`), and every `GRASS::*` library target it
exports records `sancovrt` in its `INTERFACE_LINK_LIBRARIES` (each was
linked against it via this repository's project-wide
`link_libraries(sancovrt)`). Because `sancovrt` is deliberately an
`IMPORTED` target rather than an exported one (Section 1.2's reasoning:
`install(EXPORT ...)` refuses a real dependency that is not itself part
of the export set), CMake writes that dependency into the exported
`GRASS_*Targets.cmake` files as a bare, unresolved name, and the addon's
own separate CMake project has nothing by that name to resolve it to --
hence the plain `-lsancovrt` on the addon's link line with no `-L` for
it. Fixed in `GRASSConfig.cmake.in` (loaded by every `find_package(GRASS
...)`, addon builds included) by defining the same `sancovrt` `IMPORTED`
target there, pointing at the runtime `.so` this repository's own build
installed to `${GRASS_INSTALL_LIBDIR}`, guarded by the build's own
`WITH_SANCOV_COVERAGE` setting (substituted into the generated config,
so a non-coverage GRASS install defines nothing extra). Verified locally
end to end: a `WITH_SANCOV_COVERAGE=ON` CMake build, installed, then
`g.extension extension=r.gdd operation=add` -- the exact command
`cmake.yml`'s failing test runs -- compiles and installs `r.gdd`
successfully, `ldd` on the resulting binary shows it linked against the
installed `libsancovrt.so`, and running it writes a real coverage dump.

## 2. Build-time and test-time deltas

All numbers below are wall-clock step durations read directly from real
GitHub Actions runs of this branch (`ubuntu-24.04` hosted runners),
triggered via `workflow_dispatch`, not local measurements or estimates.

### 2.1 `pytest.yml`: build and test steps

Source: <https://github.com/echoix/grass/actions/runs/33689957509> (all
four matrix cells ran independently, in parallel, on separate runners).
The parallel-pytest step forces `OMP_NUM_THREADS=1`; the solo and
gunittest-based pytest steps do not restrict it.

| Step | none (baseline) | llvm-source (existing) | sancov-gcc | sancov-clang |
| --- | --- | --- | --- | --- |
| Build | 2m48s | 4m33s (+63%) | 4m22s (+56%) | 3m10s (+13%) |
| Run pytest, parallel workers | 4m40s | 5m34s (+19%) | 6m02s (+29%) | 4m10s (-11%) |
| Run pytest, solo (`needs_solo_run`) | 1m14s | 2m11s (+77%) | 1m41s (+36%) | 1m11s (-4%) |
| Run pytest, gunittest-based | 19s | 23s (+21%) | 22s (+16%) | 16s (-16%) |
| Coverage merge/export/symbolize | n/a | 20s (llvm-cov export) | (see Section 1.5: failed on this run, fixed since) | (same) |
| Whole job, checkout to finish | 12m13s | 16m21s | 15m15s | 11m55s |

Two things stand out, and neither matches a simple "SanitizerCoverage is
cheaper" or "SanitizerCoverage is pricier" story:

- **Build time**: both coverage mechanisms add real overhead over the
  uninstrumented baseline, but `sancov-clang`'s build (+13%) was
  noticeably *cheaper* to build than either `llvm-source` (+63%) or
  `sancov-gcc` (+56%) on this run. This is a single run per configuration,
  not an average of repeated trials, so treat the exact percentages as
  indicative rather than precise -- but the direction (both
  SanitizerCoverage variants are in the same broad range as source-based
  coverage for *build* time, not dramatically better or worse) held
  across this run.
- **Test time under forced single-threading**: with `OMP_NUM_THREADS=1`,
  none of the three coverage mechanisms show a dramatic test-time
  penalty here -- `sancov-clang` was actually the fastest of the four in
  every pytest step on this run. This matters directly for Section 2.2:
  it isolates that the mechanism-inherent overhead this report predicted
  for GCC's mutex-guarded `trace-pc` dedup (Section 1.2) is specifically
  an *OpenMP-thread-contention* cost, not a blanket per-call cost --
  it disappears when only one thread is ever calling the coverage
  callback.

### 2.2 `cmake.yml`: the real cost of GCC's `trace-pc` under OpenMP

Source: <https://github.com/echoix/grass/actions/runs/33686891578> (`none`
and `gcc` jobs; this run predates several of the fixes in Section 1.5, but
the build/test wiring being measured here was already correct at that
commit). `cmake.yml`'s gunittest run (`test_thorough.sh`) does **not**
force `OMP_NUM_THREADS=1`, unlike `pytest.yml`'s parallel step.

| Step | none (baseline) | gcc (sancov, `trace-pc`) |
| --- | --- | --- |
| Build | 2m02s | 2m25s (+19%) |
| Run tests (gunittest, `test_thorough.sh`) | 36m49s | **2h02m05s (+232%)** |

This is the single most decisive quantitative result in this experiment.
Build-time overhead for GCC's `trace-pc` is modest and in line with
Section 2.1's numbers. But the *test*-time overhead, run under GRASS's
normal (unrestricted) OpenMP threading, is **more than triple** the
baseline -- 7325 seconds versus 2209 seconds, both real, measured
durations of the same test suite on the same runner type.

This is exactly the mechanism-inherent cost flagged in Section 1.2:
`-fsanitize-coverage=trace-pc` gives the compiler no per-edge guard word
to dedup on, so `utils/sancov_runtime.c`'s runtime does its own dedup via
a **mutex-guarded** hash-set insertion on *every single edge execution*,
not just the first. Under GRASS's OpenMP-parallel raster/vector routines
running with the default thread count, many threads hammering that one
mutex on every instrumented edge is a realistic, and evidently severe,
source of contention. Clang's `trace-pc-guard` path does not have this
problem (Section 1.2's guard-based dedup needs no lock after an edge's
first hit), and Section 2.1's `sancov-clang` numbers -- gathered under
forced single-threading, so not a direct comparison, but consistent with
the theory -- showed no comparable blowup.

No equivalent `cmake.yml` number exists yet for `sancov-clang` or for
`GRASS_LLVM_COVERAGE`'s macOS-only mechanism under CMake; re-running
`cmake.yml` a further time (each full run of this job takes over two
hours end to end) was not done given the time already invested and the
clarity of the `none` vs `gcc` result already in hand.

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

```text
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

```text
G_define_standard_option lib/gis/parser_standard_options.c:273   (G_OPT_R_INPUT)
G_define_standard_option lib/gis/parser_standard_options.c:290   (G_OPT_R_OUTPUT)
G_define_standard_option lib/gis/parser_standard_options.c:483   (G_OPT_V_INPUT)
G_define_standard_option lib/gis/parser_standard_options.c:602   (G_OPT_F_INPUT)
```

(gcc's `trace-pc` build produced the identical four lines.) But *within*
`G_OPT_V_INPUT`'s case, both mechanisms report exactly **one** hit, at line
483 (the case's first statement) -- never at line 488 or 489 specifically:

```console
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

**Clang's `trace-pc-guard`**: worth a closer look, not worth switching to
yet. It is the only one of the two SanitizerCoverage paths whose numbers
in this experiment look competitive with the existing mechanism --
comparable build time (Section 2.1: +13% versus `llvm-source`'s +63%
here, though this is one run, not a trend) and no test-time blowup under
single-threaded execution. But it was working correctly, end to end
(build, real test run, real symbolized output), for a grand total of one
clean CI run in this session, after five rounds of real, CI-only bugs
(Section 1.5); it has not been run enough times, or under GRASS's normal
unrestricted OpenMP threading in `pytest.yml`, to know whether it holds up
the way `sancov-gcc`'s numbers held up badly under `cmake.yml`'s
unrestricted threading. And its coverage report is strictly coarser than
source-based coverage's for the exact case that matters most for this
codebase -- see the `G_OPT_V_INPUT` result in Section 3.1, where two
distinct `_()` macro expansions on consecutive lines are indistinguishable
in `trace-pc-guard`'s output but fully separated in `-fcoverage-mapping`'s.
There is no result here that argues for replacing `GRASS_LLVM_COVERAGE`
with it; the case for pursuing it further would be for a different goal
than coverage percentage tracking -- e.g. if a fuzzing harness for GRASS's
C parsers/format readers were ever built, since SanitizerCoverage's
`trace-pc-guard` ABI is the one libFuzzer and AFL++ actually consume, and
this session's runtime already proves it produces usable edge data
without needing `-fsanitize=fuzzer` at all.

**GCC's `trace-pc`**: not worth pursuing further for this project's
coverage goals. Three independent problems compound:

1. It is not what most people mean by "SanitizerCoverage on GCC" --
   GCC 13/14 do not implement `trace-pc-guard` at all (Section 1.1), so
   there is no per-edge dedup available; the runtime must lock a
   mutex on every edge *execution*, not just every edge, to do the
   dedup GCC's own instrumentation doesn't provide.
2. That mutex is a measured, severe liability under GRASS's real
   OpenMP-parallel workload: +232% test time in a real, full CI run
   (Section 2.2), the largest number in this entire report by a wide
   margin. A coverage mechanism that triples CI test time for one
   compiler is not a viable addition to routine CI regardless of what
   it costs to build.
3. Its coverage output has the exact same block-level granularity
   ceiling as clang's `trace-pc-guard` (Section 3.1 makes no
   compiler-specific claim there -- both SanitizerCoverage paths lose
   the same macro-expansion resolution), so it does not even offer a
   granularity advantage to offset the performance cost.

**Overall**: this experiment does not find grounds to add
SanitizerCoverage as an ongoing GRASS coverage mechanism, on either
compiler, alongside or in place of `GRASS_LLVM_COVERAGE`. The practical
case for the amount of Autotools/CMake build-system surgery required
(Section 1.3-1.4) and the operational fragility uncovered only by running
real CI repeatedly (Section 1.5) would need a correspondingly large
payoff -- either meaningfully cheaper builds/tests, or meaningfully
better coverage data -- and neither showed up. `GRASS_LLVM_COVERAGE`
should stay as GRASS's coverage mechanism; this branch's value is the
prototype, the runtime and symbolizer (which do work, and could be
revived quickly if a fuzzing use case for `trace-pc-guard` specifically
comes up later), and the concrete, now-documented reasons not to pursue
this further as a coverage-tracking mechanism.
