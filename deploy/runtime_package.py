"""Strict complete-package construction and actual mounted-package verification."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile

import chat_deploy as c

SOURCE = "2a6ff85491edf60ac2d29c23d4ddad558e47716cef4ed2ad69d991de7a7e1c2c"
SOURCE_ZIP = "cd4ce8db32214ba2cd30428984910bc0a7c77a68c76e5521e2717a775d5d5429"
MANIFEST = c.ARTIFACTS / "run-package-manifest.json"
BUILD = c.ARTIFACTS / "run-package-build/source"

def safe_path(path):
    path = Path(path)
    c.require(path.is_relative_to(c.ROOT), "Path outside project.")
    for parent in (path, *path.parents):
        c.require(not parent.is_symlink(), "Linked operational path forbidden.")
        if parent == c.ROOT:
            break
    return path


def digest(value):
    return hashlib.sha256(value).hexdigest()

def credential_signature(data):
    # Key parsers contain the PEM label as a literal; key material also needs a body.
    pem = rb"-----BEGIN [A-Z ]*PRIVATE KEY-----(?:\r?\n|\\n)[A-Za-z0-9+/=]{32,}"
    return bool(re.search(pem, data) or any(re.search(p, data) for p in c.SECRET_PATTERNS[1:3]))


def allowed(name):
    p = PurePosixPath(name)
    return (not p.is_absolute() and ".." not in p.parts and "\\" not in name
            and all(not part.startswith(".env") and part not in
                    (".npmrc", ".git", ".bin", "__pycache__") for part in p.parts)
            and (name in ("package.json", "package-lock.json")
                 or name.startswith(("dist/client/", "dist/server/", "node_modules/"))))


def package():
    files, source = c.source_manifest()
    safe_path(BUILD)
    c.require(source == SOURCE and digest(safe_path(c.package_path(source)).read_bytes()) == SOURCE_ZIP,
              "Frozen source or source ZIP changed.")
    for name in ("package.json", "package-lock.json"):
        c.require(safe_path(BUILD / name).read_bytes() == files[name], "Linux package metadata drift.")
    compiled = json.loads(safe_path(c.ARTIFACTS / "static-recovery-before-proof.json").read_text())
    for name, pin in compiled["compiled_server_sha256"].items():
        c.require(digest(safe_path(BUILD / name).read_bytes()) == pin, "Linux compiled backend drift.")
    for path in (c.SOURCE / "dist/client").rglob("*"):
        if path.is_file():
            relative = path.relative_to(c.SOURCE)
            c.require(safe_path(BUILD / relative).read_bytes() == safe_path(path).read_bytes(), "Linux reviewed UI drift.")
    c.require(not any((BUILD / "node_modules" / name).exists()
                      for name in ("vite", "tsx", "typescript")), "Dev-only tooling in production tree.")
    values = {}
    for path in sorted(BUILD.rglob("*")):
        name = path.relative_to(BUILD).as_posix()
        if not allowed(name):
            continue
        c.require(not path.is_symlink(), "Linked runtime entry forbidden.")
        if path.is_dir():
            continue
        c.require(not path.is_symlink() and path.is_file() and path.suffix != ".node",
                  "Linked/native package entry requires separate target review.")
        data = path.read_bytes()
        c.require(not data.startswith((b"\x7fELF", b"MZ", b"\xcf\xfa\xed\xfe")),
                  "Native executable requires separate Linux target review.")
        c.require(not credential_signature(data),
                  "Credential signature in runtime package.")
        values[name] = data
    c.require("node_modules/@azure/ai-projects/package.json" in values and
              "dist/client/index.html" in values and "dist/server/index.js" in values,
              "Runtime package incomplete.")
    manifest = {name: {"sha256": digest(data), "bytes": len(data)} for name, data in values.items()}
    c.require(not MANIFEST.exists(), "Runtime manifest already exists.")
    MANIFEST.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    target = c.ARTIFACTS / "run-package-staged.zip"
    with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in values.items():
            info = zipfile.ZipInfo(name, (2026, 10, 27, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o444) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    pin = digest(target.read_bytes())
    final = c.ARTIFACTS / ("redshift-chat-runtime-" + pin + ".zip")
    c.require(not final.exists(), "Immutable runtime package already exists.")
    target.rename(final)
    with zipfile.ZipFile(final) as archive:
        c.require(len(archive.namelist()) == len(values) and
                  set(archive.namelist()) == set(manifest) and
                  all(allowed(name) and archive.read(name) == data for name, data in values.items()),
                  "Reopened runtime ZIP mismatch.")
    proof = {"source_sha256": SOURCE, "source_zip_sha256": SOURCE_ZIP,
             "runtime_package_sha256": pin, "runtime_manifest_sha256": c.sha(manifest),
             "runtime_package_path": str(final.relative_to(c.ROOT)),
             "entry_count": len(manifest), "bytes": final.stat().st_size,
             "native_dependencies": "none; .node entries rejected",
             "linux_builder_image": "node@sha256:55fb5f5a527ea2c5c4a95f963e48ef90aa38c7b346054fdc8ee9957a2b55d205"}
    (c.ARTIFACTS / "run-package-artifact-proof.json").write_text(json.dumps(proof, indent=2) + "\n")
    return proof


def validate_artifact(proof):
    c.require(c.source_manifest()[1] == SOURCE and
              digest(safe_path(c.package_path(SOURCE)).read_bytes()) == SOURCE_ZIP,
              "Frozen source ZIP drift.")
    manifest = json.loads(safe_path(MANIFEST).read_text())
    c.require(c.sha(manifest) == proof["runtime_manifest_sha256"], "Runtime manifest changed.")
    target = safe_path(c.ROOT / proof["runtime_package_path"])
    c.require(digest(target.read_bytes()) == proof["runtime_package_sha256"], "Runtime package changed.")
    with zipfile.ZipFile(target) as archive:
        c.require(len(archive.infolist()) == len(manifest) and set(archive.namelist()) == set(manifest),
                  "Runtime archive entry-set mismatch.")
        for info in archive.infolist():
            c.require(allowed(info.filename) and stat.S_ISREG(info.external_attr >> 16),
                      "Unsafe runtime archive entry.")
            data = archive.read(info)
            c.require(manifest[info.filename] == {"sha256": digest(data), "bytes": len(data)},
                      "Runtime archive/manifest content mismatch.")
    return manifest


REPORT = """import os,stat,json,hashlib,re,sys
base='/home/site/wwwroot'
r={'readonly':bool(os.statvfs(base).f_flag & os.ST_RDONLY),'namespace':os.readlink('/proc/self/ns/mnt')}
with open('/home/data/SitePackages/packagename.txt') as f:name=f.read(129).strip()
assert re.fullmatch('[A-Za-z0-9_.-]{1,128}[.]zip',name)
r['package_name']=name
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
r['package_sha256']=sha('/home/data/SitePackages/'+name)
r['processes']=[]
for value in os.listdir('/proc'):
 if not value.isdigit():continue
 p='/proc/'+value
 try:
  with open(p+'/comm') as f:comm=f.read(80).strip()
  if not (comm.startswith('node') or comm=='MainThread'):continue
  with open(p+'/cmdline','rb') as f:args=f.read(257)
  if args not in (b'node'+bytes([0])+b'dist/server/index.js'+bytes([0]),b'/usr/local/bin/node'+bytes([0])+b'dist/server/index.js'+bytes([0])):continue
  with open(p+'/stat','rb') as f:fields=f.read(4096).rpartition(b') ')[2].split()
  if len(fields)>=50 and os.readlink(p+'/cwd')==base:
   r['processes'].append({'pid':int(value),'start_ticks':int(fields[19]),'namespace':os.readlink(p+'/ns/mnt')})
 except OSError:continue
if r['readonly'] and not (len(sys.argv)>1 and sys.argv[1]=='scm'):
 entries={}
 for root,dirs,files in os.walk(base,followlinks=False):
  assert not any(os.path.islink(root+'/'+n) for n in dirs)
  for name in files:
   p=root+'/'+name;relative=os.path.relpath(p,base)
   assert not any(v.startswith('.env') or v in ('.npmrc','.git') for v in relative.split('/'))
   assert stat.S_ISREG(os.lstat(p).st_mode)
   entries[relative]={'sha256':sha(p),'bytes':os.stat(p).st_size}
 r['entries']=entries
print(json.dumps(r,separators=(',',':')))
"""


def verify_mount(state):
    manifest = json.loads(MANIFEST.read_text())
    c.require(c.sha(manifest) == state.get("runtime_manifest_sha256"), "Runtime manifest pin changed.")
    c.require(not any(char in REPORT for char in ('"', "$", "`", "\\")), "Unsafe report command.")
    result = c.request("POST", "https://" + c.APP + ".scm.azurewebsites.net/api/command",
                       {"command": 'python3 -c "' + REPORT + '" scm', "dir": "/home"},
                       scope="https://management.azure.com/.default", timeout=180)
    c.require(result.get("ExitCode") == 0, "Mounted package inspection failed; no success assumed.")
    scm_report = json.loads(result["Output"])
    c.require(scm_report.get("package_sha256") == state.get("zip_sha256"), "SCM package pointer/hash mismatch.")
    report = worker_report()
    c.require(report.get("readonly") is True and report.get("package_sha256") == state.get("zip_sha256")
              and report.get("entries") == manifest and len(report.get("processes", [])) == 1
              and report["processes"][0]["namespace"] == report["namespace"],
              "Actual worker readonly mounted package differs.")
    (c.ARTIFACTS / "run-package-mounted-proof.json").write_text(json.dumps({
        "status": "passed", "package_sha256": report["package_sha256"],
        "runtime_manifest_sha256": c.sha(manifest), "entry_count": len(manifest),
        "readonly": True, "package_name": report["package_name"],
        "actual_worker_process": report["processes"][0],
        "scm_package_matches": True,
    }, indent=2) + "\n")
    return report


def worker_report():
    import logging
    import threading
    from types import SimpleNamespace
    from azure.cli.core import get_default_cli
    from azure.cli.command_modules.appservice import custom
    from fabric import Connection
    logging.disable(logging.CRITICAL)
    answer = {}
    done = threading.Event()
    def observe(hostname, port, username, authentication):
        connection = None
        try:
            connection = Connection(host=hostname, port=port, user=username,
                                    connect_kwargs={"password": authentication}, connect_timeout=10)
            value = connection.run('python3 -c "' + REPORT + '"', hide=True, warn=True,
                                   pty=False, in_stream=False, timeout=150)
            if value.exited == 0:
                answer.update(json.loads(value.stdout))
        except Exception as error:
            answer["safe_error_class"] = type(error).__name__
        finally:
            if connection is not None:
                connection.close()
            done.set()
    custom._start_ssh_session = observe
    cli = get_default_cli()
    c.require(cli.invoke(["account", "show", "--query", "{id:id,tenantId:tenantId}", "--output", "none"]) == 0
              and cli.result.result == {"id": c.SUB, "tenantId": c.TENANT}, "Worker transport context mismatch.")
    instances = c.arm("GET", c.APP_ID + "/instances", c.WEB_API)["value"]
    c.require(len(instances) == 1, "Worker attribution requires one instance.")
    custom.create_tunnel_and_session(SimpleNamespace(cli_ctx=cli), c.RG, c.APP, timeout=180)
    c.require(done.wait(2) and "entries" in answer, "Actual worker package observation failed.")
    return answer


if __name__ == "__main__":
    print(json.dumps(package(), indent=2))
