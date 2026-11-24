"""Plan Step 10.1: assemble submission/ (report PDF, slides PPTX, code zip). Run: python analysis/package.py"""
import os
import shutil
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SUB = os.path.join(ROOT, "submission")
NAME = "FinalProject_2026_CTierney"
INCLUDE = ["model/DataCenterSD.nlogox", "model/build_nlogox.py", "data", "notes/model_spec.md", "notes/demo_script.md", "experiments",
           "analysis", "figures", "report/build_report.py", "slides/build_slides.py"]
SKIP_DIRS = {"__pycache__", "render"}
SKIP_EXT = {".pyc", ".class"}


def files():
    for item in INCLUDE:
        p = os.path.join(ROOT, item)
        if os.path.isfile(p):
            yield p
            continue
        for d, dirs, fs in os.walk(p):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
            for f in fs:
                if os.path.splitext(f)[1] not in SKIP_EXT:
                    yield os.path.join(d, f)


def main():
    os.makedirs(SUB, exist_ok=True)
    shutil.copy(os.path.join(ROOT, "report", NAME + ".pdf"), os.path.join(SUB, NAME + ".pdf"))
    shutil.copy(os.path.join(ROOT, "slides", NAME + ".pptx"), os.path.join(SUB, NAME + ".pptx"))
    zp = os.path.join(SUB, NAME + ".zip")
    n = 0
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join(SUB, "README.md"), NAME + "/README.md")
        for f in files():
            z.write(f, NAME + "/" + os.path.relpath(f, ROOT).replace("\\", "/"))
            n += 1
    print("wrote %s (%d files, %.1f MB)" % (zp, n + 1, os.path.getsize(zp) / 1e6))


if __name__ == "__main__":
    main()
