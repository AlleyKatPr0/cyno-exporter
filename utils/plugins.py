import os, subprocess


class Plugins:
    def __init__(self, *plugin):
        self.cwd = "./tools"
        self.exe = os.path.join(self.cwd, *plugin)

    def run(self, *args):
        # Determine subprocess arguments based on the operating system.
        # ``creationflags=subprocess.CREATE_NO_WINDOW`` is only available on
        # Windows. On other platforms, attempting to use it raises an
        # ``AttributeError``. Detect ``os.name`` and only supply the flag on
        # Windows to ensure cross-platform compatibility.
        kwargs = {
            "check": False,
            "capture_output": True,
            "text": True,
        }

        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        stdout = subprocess.run([self.exe, *args], **kwargs).stdout
        return stdout


class Gr2ToJson(Plugins):
    def __init__(self):
        super().__init__("gr2tojson", "gr2tojson.exe")

    def run(self, *args):
        super().run(*args)


class Revorb(Plugins):
    def __init__(self):
        super().__init__("revorb", "revorb.exe")

    def run(self, *args):
        super().run(*args)


class NvttExport(Plugins):
    def __init__(self):
        super().__init__("nvidia", "nvtt_export.exe")

    def run(self, *args):
        filename = os.path.splitext(args[0])[0]
        dir_path = os.path.dirname(args[0])
        super().run(args[0], "-o", os.path.join(dir_path, f"{filename}.png"))


class Ww2Ogg(Plugins):
    def __init__(self):
        super().__init__("ww2ogg", "ww2ogg.exe")

    def run(self, *args):
        filename = os.path.splitext(args[0])
        dest = os.path.dirname(args[0])
        old = os.path.join(dest, f"{filename[0]}{filename[1]}")
        new = os.path.join(dest, f"{filename[0]}.ogg")
        stdout = super().run(
            old,
            "-o",
            new,
            "--pcb",
            os.path.join(self.cwd, "ww2ogg", "packed_codebooks_aoTuV_603.bin"),
        )
        if "Parse error" in stdout:
            return stdout, new
        return None, new
