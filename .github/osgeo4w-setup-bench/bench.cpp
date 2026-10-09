// Benchmark harness that mimics how the OSGeo4W setup (a fork of the Cygwin
// setup 2.579) extracts a .tar.bz2 package, so that individual parts of the
// pipeline can be varied and timed on Windows.
//
// The code paths mirror src/setup of https://github.com/jef-n/OSGeo4W:
//   BzReader      <- compress_bz::read (bzip2 fed by fread() in small chunks)
//   tar loop      <- archive_tar::next_file_name / archive_tar_file::read
//   file handling <- archive::extract_file, io_stream_cygfile, mkdir_p
//   UI updates    <- Installer::installOne (SetText3 + progress per file)
//
// Usage:
//   bench decomp <pkg.tar.bz2> [--in N]
//   bench extract <pkg.tar.bz2> <destdir> [--in N] [--copy N] [--ui 0|1]
//
// --in    bytes requested per fread() of the compressed file (setup: 4096)
// --copy  chunk size of the tar -> file copy loop (setup: 16384)
// --ui    send the per-file cross-thread window messages the setup sends

#include <windows.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <string>
#include <vector>

#include "bzlib.h"

typedef SSIZE_T ssize_t;

static double now_s()
{
  LARGE_INTEGER f, c;
  QueryPerformanceFrequency(&f);
  QueryPerformanceCounter(&c);
  return (double)c.QuadPart / (double)f.QuadPart;
}

// Same structure as compress_bz::read in src/setup/compress_bz.cc.
class BzReader
{
public:
  BzReader(const char *path, size_t inchunk) : inchunk(inchunk), buf(inchunk)
  {
    fp = fopen(path, "rb");
    memset(&strm, 0, sizeof strm);
    if (!fp || BZ2_bzDecompressInit(&strm, 0, 0) != BZ_OK) {
      fprintf(stderr, "cannot open %s\n", path);
      exit(2);
    }
  }
  ~BzReader()
  {
    BZ2_bzDecompressEnd(&strm);
    fclose(fp);
  }

  ssize_t read(void *buffer, size_t len)
  {
    if (endReached || len == 0)
      return 0;
    strm.avail_out = (unsigned)len;
    strm.next_out = (char *)buffer;
    ssize_t rlen = 1;
    while (true) {
      int ret = BZ2_bzDecompress(&strm);
      if (strm.avail_in == 0 && rlen > 0) {
        rlen = (ssize_t)fread(buf.data(), 1, inchunk, fp);
        strm.avail_in = (unsigned)rlen;
        strm.next_in = buf.data();
      }
      if (ret != BZ_OK && ret != BZ_STREAM_END)
        return -1;
      if (ret == BZ_OK && rlen == 0 && strm.avail_out)
        return -1;
      if (ret == BZ_STREAM_END) {
        endReached = true;
        return (ssize_t)(len - strm.avail_out);
      }
      if (strm.avail_out == 0)
        return (ssize_t)len;
    }
  }

  long tell() { return ftell(fp); }

private:
  FILE *fp = nullptr;
  bz_stream strm;
  size_t inchunk;
  std::vector<char> buf;
  bool endReached = false;
};

// Reads exactly len bytes unless the stream ends (archive_tar_file::read).
static bool read_full(BzReader &r, void *dst, size_t len)
{
  char *p = (char *)dst;
  while (len > 0) {
    ssize_t got = r.read(p, len);
    if (got <= 0)
      return false;
    p += got;
    len -= got;
  }
  return true;
}

// Copy of mkdir_p in src/setup/mkdir.cc (narrow-character variant).
static int mkdir_p(int isadir, const char *cpath)
{
  std::string copy(cpath);
  char *path = &copy[0];
  char saved_char, *slash = 0;
  char *c;
  DWORD d, gse;

  d = GetFileAttributesA(path);
  if (d != INVALID_FILE_ATTRIBUTES && d & FILE_ATTRIBUTE_DIRECTORY)
    return 0;

  if (isadir) {
    if (CreateDirectoryA(path, 0))
      return 0;
    gse = GetLastError();
    if (gse != ERROR_PATH_NOT_FOUND && gse != ERROR_FILE_NOT_FOUND)
      return 1;
  }

  for (c = path; *c; c++) {
    if (*c == ':')
      slash = 0;
    if (*c == '/' || *c == '\\')
      slash = c;
  }
  if (!slash)
    return 0;
  if (((slash - path) == 2) && (path[1] == ':'))
    return 1;

  saved_char = *slash;
  *slash = 0;
  if (mkdir_p(1, path)) {
    *slash = saved_char;
    return 1;
  }
  *slash = saved_char;
  if (!isadir)
    return 0;
  return mkdir_p(isadir, path);
}

// io_stream_file::remove / io_stream_cygfile::remove for a missing file.
static void remove_existing(const char *path)
{
  DWORD w = GetFileAttributesA(path);
  if (w == INVALID_FILE_ATTRIBUTES)
    return;
  SetFileAttributesA(path, w & ~FILE_ATTRIBUTE_READONLY);
  DeleteFileA(path);
}

// io_stream_cygfile::set_mtime: the stream is closed, then reopened.
static void set_mtime(FILE *fp, const char *path, time_t mtime)
{
  const long long FACTOR = 0x19db1ded53ea710LL;
  const long long NSPERSEC = 10000000LL;
  fclose(fp);
  long long ftimev = mtime * NSPERSEC + FACTOR;
  FILETIME ftime;
  ftime.dwHighDateTime = (DWORD)(ftimev >> 32);
  ftime.dwLowDateTime = (DWORD)(ftimev & 0xffffffff);
  HANDLE h = CreateFileA(path, GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE,
                         0, OPEN_EXISTING,
                         FILE_ATTRIBUTE_NORMAL | FILE_FLAG_BACKUP_SEMANTICS, 0);
  if (h != INVALID_HANDLE_VALUE) {
    SetFileTime(h, 0, 0, &ftime);
    CloseHandle(h);
  }
}

// The setup updates its progress page from the installer thread while the GUI
// thread pumps messages, so every call below is a synchronous cross-thread
// message. A visible STATIC control is used when a desktop is available.
static HWND g_hwnd = nullptr;
static bool g_visible = false;

static DWORD WINAPI ui_thread(LPVOID ready)
{
  g_hwnd = CreateWindowExA(0, "STATIC", "", WS_POPUP | WS_VISIBLE | SS_LEFT, 0,
                           0, 600, 20, NULL, NULL, GetModuleHandle(NULL), NULL);
  g_visible = g_hwnd != nullptr;
  if (!g_hwnd)
    g_hwnd = CreateWindowExA(0, "STATIC", "", 0, 0, 0, 0, 0, HWND_MESSAGE, NULL,
                             GetModuleHandle(NULL), NULL);
  SetEvent((HANDLE)ready);
  MSG msg;
  while (GetMessage(&msg, NULL, 0, 0) > 0) {
    TranslateMessage(&msg);
    DispatchMessage(&msg);
  }
  return 0;
}

static void ui_update(const std::string &name, long done, long total)
{
  // Installer::installOne: SetText3 per file, then progress(): SetBar1,
  // SetBar2 and the window title.
  int pct = total > 0 ? (int)(100.0 * done / total) : 0;
  SetWindowTextA(g_hwnd, name.c_str());
  SendMessageA(g_hwnd, WM_USER, pct, 0);
  SendMessageA(g_hwnd, WM_USER, pct, 0);
  SetWindowTextA(g_hwnd, (std::to_string(pct) + "% - OSGeo4W Setup").c_str());
}

struct Options {
  size_t in = 4096;
  size_t copy = 16384;
  int ui = 0;
};

static int do_decomp(const char *pkg, const Options &o)
{
  BzReader r(pkg, o.in);
  std::vector<char> buf(65536);
  long long bytes = 0;
  ssize_t got;
  double t0 = now_s();
  while ((got = r.read(buf.data(), buf.size())) > 0)
    bytes += got;
  double t1 = now_s();
  printf("RESULT mode=decomp in=%zu bytes=%lld secs=%.3f\n", o.in, bytes,
         t1 - t0);
  return got < 0;
}

static int do_extract(const char *pkg, const char *dest, const Options &o)
{
  if (o.ui) {
    HANDLE ready = CreateEvent(NULL, TRUE, FALSE, NULL);
    CreateThread(NULL, 0, ui_thread, ready, 0, NULL);
    WaitForSingleObject(ready, 10000);
  }

  BzReader r(pkg, o.in);
  WIN32_FILE_ATTRIBUTE_DATA fad;
  GetFileAttributesExA(pkg, GetFileExInfoStandard, &fad);
  long total = (long)fad.nFileSizeLow;

  std::vector<char> copybuf(o.copy);
  std::string longname;
  bool have_longname = false;
  long files = 0, dirs = 0;
  long long bytes = 0;
  char hdr[512];

  double t0 = now_s();
  while (true) {
    if (!read_full(r, hdr, sizeof hdr))
      break;
    bool allzero = true;
    for (char c : hdr)
      if (c) {
        allzero = false;
        break;
      }
    if (allzero)
      break;

    size_t size = 0;
    sscanf(hdr + 124, "%zo", &size);
    unsigned long mtime = 0;
    sscanf(hdr + 136, "%lo", &mtime);
    char type = hdr[156];

    std::string name;
    if (have_longname) {
      name = longname;
      have_longname = false;
    } else {
      name.assign(hdr, strnlen(hdr, 100));
    }

    size_t padded = (size + 511) / 512 * 512;
    if (type == 'L') {
      std::vector<char> tmp(padded);
      if (!read_full(r, tmp.data(), padded))
        break;
      longname.assign(tmp.data(), strnlen(tmp.data(), size));
      have_longname = true;
      continue;
    }
    if (type == 'x' || type == 'g' || type == '1' || type == '2') {
      std::vector<char> tmp(padded);
      if (padded && !read_full(r, tmp.data(), padded))
        break;
      continue;
    }

    std::string dst = std::string(dest) + "/" + name;
    if (o.ui)
      ui_update(name, r.tell(), total);

    if (type == '5') {
      while (!dst.empty() && dst.back() == '/')
        dst.pop_back();
      mkdir_p(1, dst.c_str());
      dirs++;
      continue;
    }

    // archive::extract_file, ARCHIVE_FILE_REGULAR.
    mkdir_p(0, dst.c_str());
    remove_existing(dst.c_str());
    FILE *out = fopen(dst.c_str(), "wb");
    if (!out) {
      fprintf(stderr, "cannot create %s\n", dst.c_str());
      return 3;
    }
    // io_stream::copy over archive_tar_file::read: each chunk is read, then
    // the tar padding of that chunk (zero except for the last one).
    size_t remaining = size;
    bool ok = true;
    if (size == 0)
      ok = true;
    while (remaining > 0 && ok) {
      size_t want = remaining < o.copy ? remaining : o.copy;
      size_t roundup = (512 - (want % 512)) % 512;
      if (!read_full(r, copybuf.data(), want)) {
        ok = false;
        break;
      }
      char throwaway[512];
      if (roundup && !read_full(r, throwaway, roundup)) {
        ok = false;
        break;
      }
      if (fwrite(copybuf.data(), 1, want, out) != want) {
        ok = false;
        break;
      }
      remaining -= want;
    }
    if (!ok) {
      fprintf(stderr, "extraction failed at %s\n", dst.c_str());
      return 4;
    }
    set_mtime(out, dst.c_str(), (time_t)mtime);
    files++;
    bytes += (long long)size;
  }
  double t1 = now_s();

  printf("RESULT mode=extract in=%zu copy=%zu ui=%d ui_visible=%d files=%ld "
         "dirs=%ld bytes=%lld secs=%.3f\n",
         o.in, o.copy, o.ui, (int)g_visible, files, dirs, bytes, t1 - t0);
  return 0;
}

int main(int argc, char **argv)
{
  if (argc < 3) {
    fprintf(stderr, "usage: bench decomp|extract pkg [dest] [options]\n");
    return 1;
  }
  std::string mode = argv[1];
  const char *pkg = argv[2];
  const char *dest = nullptr;
  int i = 3;
  if (mode == "extract") {
    if (argc < 4)
      return 1;
    dest = argv[3];
    i = 4;
  }
  Options o;
  for (; i + 1 < argc; i += 2) {
    std::string k = argv[i];
    if (k == "--in")
      o.in = (size_t)atol(argv[i + 1]);
    else if (k == "--copy")
      o.copy = (size_t)atol(argv[i + 1]);
    else if (k == "--ui")
      o.ui = atoi(argv[i + 1]);
  }
  return mode == "decomp" ? do_decomp(pkg, o) : do_extract(pkg, dest, o);
}
