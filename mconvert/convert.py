#!/usr/bin/env python3
# -*-coding: utf-8-*-

"""Convert between file types"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import sys  # pylint: disable=W0611
import shutil
import logging
import collections
import io
import itertools
import re
import datetime
import six.moves  # pylint: disable=F0401

from . import mime, utils, config, tools, display

logger = logging.getLogger(__name__)


class Tree(object):
    """Tree holding all possible conversion paths"""

    def __init__(self, fnames_orig, fname_dest, **cmd_options):
        self.cmd_options = cmd_options

        self.defaults = self.get_defaults(
            cmd_options.get("ftypes", []),
            cmd_options.get("multi", []))
        logger.debug("defaults %s", self.defaults)

        self.dest = self.parse_dest(fname_dest, fnames_orig)
        logger.debug("dest: %s", self.dest)
        logger.info(
            "Converting %s => %s (%s)",
            ",".join(self.dest["orig_fnames"]),
            self.dest["dest"],
            ",".join(self.dest["ftypes"]))

        self.brothers = None
        self.cache = [datetime.datetime.now().strftime("%Y%m%d_%H%M%S.%f"), 1]
        self.finals = [[], set()]
        self.items = [{
            "name": "",
            "ftypes": set(),
            "dirname": self.dest["dirname"]}]

    def parse_dest(self, fname_dest, fnames_orig):
        """Parse the destination"""

        dirname, filebase, extensions = utils.splitext2(fname_dest, True)
        ext = "".join(extensions)
        if fname_dest == "stdout":
            dirname = ""
            ext = None
            ftypes = {"text/plain"}
        elif ext in (".", ""):
            ftypes = {config.SETTINGS["mime_regex"]}
            ext = None
        elif (ext.startswith("." + config.SETTINGS["mime_regex"]) or
              config.SETTINGS["mime_sep"] in ext):
            ftypes = {ext[1:].replace(config.SETTINGS["mime_sep"], "/")}
            ext = None
        else:
            extensions2 = []
            for ext2 in extensions:
                extensions2.extend(
                    [".tar", ".gz"] if ext2.lower() == ".tgz" else
                    [ext2])
            ftypes = mime.get_all_ftypes(extensions2.pop(), is_ext=True)
            if extensions2:
                extra = mime.get_all_ftypes(extensions2.pop(), is_ext=True)
                if extra not in self.defaults["ftypes"]:
                    self.defaults["ftypes"].append(extra)
            if extensions2:
                logger.error("More than 2 extensions in %s", fname_dest)

        return {
            "dirname": dirname,
            "filebase": None if filebase == "" else filebase,
            "ext": ext,
            "ftypes": ftypes,
            "dest": fname_dest,
            "orig_fnames": list(tools.get_iter(fnames_orig))}

    def get_defaults(self, ftypes, multi):
        """All the convert function that have to be done"""
        defaults = {
            "steps": collections.defaultdict(list),
            "multi": set(),
            "plugins": tools.SetList(),
            "ftypes": tools.SetList()}

        for option in ftypes + multi:
            multi = set()
            plugins = set()
            ftypes = set()
            if "_" in option:
                ext_orig, ext_dest = option.split("_")
                ftypes_orig = mime.get_all_ftypes(ext_orig, is_ext=True)
                ftypes_dest = mime.get_all_ftypes(ext_dest, is_ext=True)
                found = False
                for plugin, poptions in self.get_convert_plugins():
                    if (poptions["match"](ftypes_orig) and
                            ftypes_dest.intersection(poptions["fdest"])):
                        found = True
                        plugins.add(plugin)
                        if option in multi:
                            multi.add(plugin)
                if not found:
                    logger.error("Unknown default: %s", option)
            else:
                ftypes = mime.get_all_ftypes(option, is_ext=True)
                if ftypes:
                    ftypes.update(ftypes)
                else:
                    logger.error("Unknown default: %s", option)
            if multi:
                defaults["multi"].update(multi)
            if ftypes:
                defaults["ftypes"].append(ftypes)
            if plugins:
                defaults["plugins"].append(plugins)
        return defaults

    def get_dirname(self, step):
        """Get the final dirname for conversion at step"""
        props = self.items[step]
        dirnames = [self.get_dirname(parent)
                    for parent in props.get("parents", set())]
        common_dirname = os.path.commonprefix(dirnames)
        dirname = os.path.join(common_dirname, props.get("dirname", ""))
        return os.path.normpath(dirname)

    def to_add(self, props):
        """Check if we should add this child"""
        if props["plugin"] == "lsdir":
            return True
        poptions = config.PLUGINS.get(props["plugin"], {})

        # do not apply the same convert function twice
        if props["plugin"] in props["_plugins"]:
            return False

        # this file was already this ftype before
        if props["ftypes"].intersection(props["_ftypes"]):
            # if it converts multiple files into one, no problem
            if (poptions.get("multi") or
                    props["plugin"] in self.defaults["multi"]):
                pass

            # if converting directly from this filetype, no problem
            elif props["ftypes"].intersection(
                    set.union(*[self.items[parent]["ftypes"]
                                for parent in props["parents"]])):

                pass
            # we can pass multiple time through defaults
            # elif props["ftypes"].intersection(self.defaults["ftypes"]):
            #    pass

            # if it is the final step, allow
            elif props["ftypes"].intersection(self.dest["ftypes"]):
                pass

            # otherwise, do not allow
            else:
                return False
        return True

    def add_child(self, parents, plugin, ftypes, **kwargs):
        """Add a child with properties <props> with parents <parents>"""

        for parent in parents:
            if parent in self.finals[1]:
                return None

        props = {
            "ftypes": ftypes,
            "parents": parents,
            "plugin": plugin,
            "_priority": config.PLUGINS.get(plugin, {}).get("priority", 0)}
        for key, val in kwargs.items():
            if val is not None:
                props[key] = val
        for key in ["_plugins", "_parents", "_ftypes"]:
            props[key] = set.union(*[
                self.items[parent].get(key, set()) for parent in parents])

        poptions = config.PLUGINS.get(plugin, {})
        if not self.to_add(props):
            return None

        props["_length"] = max([
            self.items[parent].get("_length", 0)
            for parent in parents]) + 1

        props["_plugins"].add(props["plugin"])
        props["_parents"].update(props["parents"])
        props["_childs"] = set()
        step = len(self.items)
        self.items.append(props)

        if (None in poptions.get("fdest", []) and
                self.cmd_options.get("unpack", False)):
            self.convert_step(step)
            props["ftypes"] = mime.get_all_ftypes(props["fullname"])
        props["_ftypes"].update(props["ftypes"])

        props["_missing"] = self.has_missing(step)
        props["_final"] = self.is_final(step, self.dest["ftypes"], True)
        if props["_final"] and props["_missing"] == 0:
            self.finals[0].append(step)
            self.fill_overlaps(step, self.finals[1])

        if self.brothers is not None:
            self.brothers.append(step)
        for parent in parents:
            self.items[parent].setdefault("_childs", set()).add(step)

        return step

    def fill_overlaps(self, step, overlaps, fill_parents=True):
        """This step has reached the end"""

        if step in overlaps:
            return
        props = self.items[step]
        overlaps.add(step)
        if self.brothers is None and fill_parents:
            if ("brothers" not in props or
                    all(brother in overlaps
                        for brother in props["brothers"])):
                for parent in props.get("parents", set()):
                    self.fill_overlaps(parent, overlaps)
        for child in props.get("_childs", set()):
            if self.items[child]["plugin"] != "lsdir":
                self.fill_overlaps(child, overlaps, False)

    def iter(self, steps):
        """Get all props for steps"""
        for step in steps:
            yield step, self.items[step]

    def is_final(self, step, ftypes, final):
        """Is this step a final step"""
        props = self.items[step]

        # this step was done manually (fast)
        if step == 0 or props.get("excluded"):
            return False

        # for a file which were not just unpacked
        if props["_priority"] != 1:  # in (0, 0.5):
            # if we can unpack it, we must do it
            for _plugin, poptions in self.get_plugins(props):
                if poptions.get("priority", 0) > 0:
                    return False

        # convert a file to itself (pdf -> pdf for example)
        if final and (
                self.cmd_options.get("same", False) and props["_length"] < 2):
            return False

        # TODO: just going through the dirs
#         if props["plugin"] == "lsdir":
#             return False

        if isinstance(ftypes, set):
            for ftype_look, ftype_file in itertools.product(
                    ftypes, props["ftypes"]):
                match = (
                    re.search(ftype_look[1:], ftype_file)
                    if ftype_look.startswith(
                        config.SETTINGS["mime_regex"]) else
                    ftype_look == ftype_file)
                if match:
                    break
        else:
            match = ftypes(props["ftypes"])
        return True if match else False

    def has_missing(self, step):
        """passes through all defaults"""

        props = self.items[step]
        missing = 0
        for plugins in self.defaults["plugins"]:
            if not plugins.intersection(props["_plugins"]):
                missing += 1
        for ftypes in self.defaults["ftypes"]:
            if not ftypes.intersection(props["_ftypes"]):
                missing += 1
        return missing

    def get_finals(self, ftypes):
        """Get all distinct final steps which have ftype"""

        steps = set()
        overlaps = set()

        for step in range(len(self.items)):
            if self.is_final(step, ftypes, False):
                steps.add(step)

        # order which goes through the defaults, and then on
        # step number
        for step in sorted(
                steps,
                key=lambda step: (self.items[step]["_missing"], step)):
            if step not in overlaps:
                self.fill_overlaps(step, overlaps)
                yield step

    def start_brothers(self):
        """Next childs to be added are brothers"""
        self.brothers = []

    def end_brothers(self):
        """All childs added were brothers"""
        if len(self.brothers) > 1:
            for brother in self.brothers:
                self.items[brother]["brothers"] = self.brothers
        if self.brothers:
            if all(brother in self.finals[0] for brother in self.brothers):
                brother = min(self.brothers)
                self.brothers = None
                for parent in self.items[brother].get("parents", set()):
                    self.fill_overlaps(parent, self.finals[1])
        self.brothers = None

    def first_step(self):
        """Add the files from the input"""
        self.start_brothers()
        for orig_fname in self.dest["orig_fnames"]:
            orig_fname = os.path.realpath(orig_fname)
            if not os.path.exists(orig_fname):
                logger.error("File %s does not exist", orig_fname)
                continue
            ftypes = mime.get_all_ftypes(orig_fname)
            self.add_child(
                [0],
                "input",
                ftypes,
                fullname=orig_fname)
        self.end_brothers()

    def expand_folders(self):
        """Expand folders"""
        size = len(self.items)
        for step, props in enumerate(self.items):
            if ("fullname" not in props or props.get("lsdir") or
                    "inode/directory" not in props["ftypes"]):
                continue
            for fname in os.listdir(props["fullname"]):
                fullname = os.path.normpath(
                    os.path.join(props["fullname"], fname))
                ftypes = mime.get_all_ftypes(fullname)
                self.add_child(
                    [step],
                    "lsdir",
                    ftypes,
                    fullname=fullname,
                    fname=fname,
                    dirname=os.path.basename(props["fullname"]))
            props["lsdir"] = True
        return len(self.items) - size

    def simple_steps(self):
        """Do one full range of simple 1-1 conversion"""

        size = len(self.items)
        for step, props in list(enumerate(self.items)):
            if props.get("simple") or props.get("excluded"):
                continue

            for plugin, poptions in self.get_plugins(props):
                if poptions.get("multi") or plugin in self.defaults["multi"]:
                    continue
                if None in poptions["fdest"]:
                    # if the output is unknown (fdest=None), the file
                    # should available
                    if "fullname" not in props:
                        self.convert_step(step)
                        props["ftypes"] = mime.get_all_ftypes(
                            props["fullname"])

                    if ":" in self.dest["ftypes"] and "fast" in poptions:
                        props["excluded"] = poptions["fast"](
                            props["fullname"],
                            self.get_dirname(step),
                            tree=self,
                            step=step)
                    else:
                        self.start_brothers()
                        for (index, fname, ftypes) in poptions["convert"](
                                props["fullname"], None, tree=self, step=step):
                            self.add_child(
                                [step],
                                plugin,
                                (mime.get_all_ftypes(fname, checkfile=False)
                                 if ftypes is None else
                                 ftypes),
                                fname=fname,
                                index=index)
                        self.end_brothers()
                else:
                    for fdest in poptions["fdest"]:
                        self.add_child(
                            [step],
                            plugin,
                            {fdest})
            props["simple"] = True
        return len(self.items) - size

    def multi_steps(self):
        """Check multiple input file types"""
        size = len(self.items)
        for plugin, poptions in self.get_convert_plugins():
            if not (poptions.get("multi") or plugin in self.defaults["multi"]):
                continue

            # only zip when the destination is reached
            # (or intermediate defaults)
            # only zip when the destination is reached
            # (or intermediate defaults)
            if (poptions.get("priority", 0) < 0 and
                    not self.dest["ftypes"].intersection(poptions["fdest"]) and
                    not any(ftypes.intersection(poptions["fdest"])
                            for ftypes in self.defaults["ftypes"])):
                continue

            orig_steps = list(self.get_finals(poptions["match"]))
            if not orig_steps or self.defaults["steps"][plugin] == orig_steps:
                continue
            self.defaults["steps"][plugin] = orig_steps
            for fdest in poptions["fdest"]:
                self.add_child(
                    orig_steps,
                    plugin,
                    {fdest})
        return len(self.items) - size

    @staticmethod
    def get_convert_plugins():
        """Get all convert plugins"""
        for plugin, poptions in sorted(
                config.PLUGINS.items(),
                key=lambda item: item[1].get("priority", 0),
                reverse=True):
            if "convert" in poptions:
                yield plugin, poptions

    def get_plugins(self, props):
        """Get all plugins which match the ftypes"""
        if props.get("excluded"):
            return
        for plugin, poptions in self.get_convert_plugins():
            # does not convert current ftype
            if not poptions["match"](props["ftypes"]):
                continue

            # do not unzip if already zipped
            if (None in poptions["fdest"] and
                    any(props["ftypes"].intersection(
                        config.PLUGINS.get(plugin2, {}).get("fdest", []))
                        for plugin2 in props["_plugins"])):
                continue

            # only zip when the destination is reached
            # (or intermediate defaults)
            if (poptions.get("priority", 0) < 0 and
                    (not self.dest["ftypes"].intersection(poptions["fdest"]) or
                     props["_missing"] > 0) and
                    not any(ftypes.intersection(poptions["fdest"])
                            for ftypes in self.defaults["ftypes"])):
                continue

            yield plugin, poptions

    def convert_step(self, step):
        """Convert between files if a path exists"""

        props = self.items[step]
        poptions = config.PLUGINS.get(props["plugin"], {})
        if "fullname" in props:
            return props["fullname"]
        orig_fnames = [
            self.convert_step(parent)
            for parent in props["parents"]]
        tools.list_remove(orig_fnames, None)
        if not orig_fnames:
            props["fullname"] = None
            return None
        if "index" in props:
            fname = props["index"]
        elif len(orig_fnames) > 1:
            common_parent = max(set.intersection(*[
                self.items[parent]["_parents"]
                for parent in props["parents"]]))
            if common_parent > 0:
                filebase = utils.splitext2(
                    self.items[common_parent]["fullname"])[1]
            else:
                filebase = "_".join([
                    utils.splitext2(orig_fname)[1]
                    for orig_fname in orig_fnames])[0:50]
            fname = filebase + mime.get_extension(props["ftypes"])
        else:
            fname = (
                (os.path.basename(orig_fnames[0])
                 if poptions.get("add_extension") else
                 utils.splitext2(orig_fnames[0])[1]) +
                mime.get_extension(props["ftypes"]))
        dest_fname = os.path.join(self.get_tmp(), fname)

        params = (
            None if ("params" not in poptions or
                     not self.cmd_options.get("menu", True)) else
            poptions["params"](
                orig_fnames[0] if len(orig_fnames) == 1 else orig_fnames)
            if callable(poptions["params"]) else
            poptions["params"])
        if params is not None:
            self.menu_params(
                "{0} => {1}".format(
                    ",".join([
                        os.path.basename(orig_fname)
                        for orig_fname in orig_fnames]),
                    os.path.basename(dest_fname)),
                params)
        print(step, orig_fnames[0], dest_fname)
        dest_result = poptions["convert"](
            orig_fnames[0] if len(orig_fnames) == 1 else orig_fnames,
            dest_fname,
            tree=self,
            step=step)
        if isinstance(dest_result, tuple):
            props["dirname"], dest_fname = dest_result
        else:
            dest_fname = dest_result
        logger.info(
            "%s => %s (%s)",
            ",".join(orig_fnames),
            dest_fname,
            props["plugin"])
        props["fullname"] = dest_fname
        return props["fullname"]

    def get_tmp(self, main=False):
        """Get temporary directory"""
        if main:
            return os.path.join(
                config.SETTINGS["tmp_dir"],
                self.cache[0])
        tmp_dir = os.path.join(
            config.SETTINGS["tmp_dir"],
            self.cache[0],
            "{0:02d}".format(self.cache[1]))
        tools.create_dir(tmp_dir, is_dir=True, remove=True)
        self.cache[1] += 1
        return tmp_dir

    def save(self, step):
        """Final conversion"""

        extra = None
        tmp_name = self.convert_step(step)
        if isinstance(tmp_name, list):
            extra = tmp_name
            tmp_name = tmp_name[0]
        if tmp_name is None or not os.path.exists(tmp_name):
            return None

        if self.dest["dest"] == "stdout":
            with io.open(tmp_name, "r") as fobj:
                sys.stdout.write(fobj.read())
            return None

        dirname = (self.get_dirname(step) if self.dest["filebase"] is None else
                   self.dest["dirname"])
        if os.path.isdir(tmp_name):
            final = os.path.join(dirname, os.path.basename(tmp_name))
        else:
            _, filebase, ext = utils.splitext2(tmp_name, is_file=True)
            filebase = (filebase if self.dest["filebase"] is None else
                        self.dest["filebase"])
            ext = ext if self.dest["ext"] is None else self.dest["ext"]
            final = os.path.normpath(os.path.join(dirname, filebase + ext))

        if tmp_name == final:
            return None

        try:
            if os.path.isdir(tmp_name):
                logger.info("%s -> %s (copydir)", tmp_name, final)
                tools.create_dir(final, is_dir=True)
                shutil.copystat(tmp_name, final)
            else:
                if not self.cmd_options.get("overwrite", False):
                    final = utils.get_available(final)
                logger.info("%s -> %s (copy)", tmp_name, final)
                tools.create_dir(final, is_file=True)
                shutil.copy2(tmp_name, final)
        except IOError:
            logger.error("Error: cannot save %s", final)
            return None

        if extra is not None:
            self.copy_extra(extra, final)
        return final

    @staticmethod
    def copy_extra(extra, final):
        """Copy the extra files, also translate to new final filebase"""

        final_base = os.path.splitext(os.path.basename(final))[0]
        dest_base = os.path.splitext(os.path.basename(extra[0]))[0]
        final_dir = os.path.dirname(final)
        for fname in extra[1:]:
            if not os.path.exists(fname):
                logger.error("No such file: %s", fname)
                continue
            file_base, file_ext = os.path.splitext(os.path.basename(fname))
            if file_base == dest_base:
                new_name = final_base + file_ext
            else:
                new_name = file_base + file_ext
            shutil.copy2(fname, os.path.join(final_dir, new_name))

    def save_all(self):
        """Save all files"""

        fnames = []
        dir_times = []
        orig_steps = {
            step for step in self.items[0].get("_childs", set())
            if not self.items[step].get("excluded")}

        for step, props in self.iter(self.finals[0]):
            if step in orig_steps:
                orig_steps.remove(step)
                # continue if ftype(orig) == ftype(dest)
            orig_steps.difference_update(props["_parents"])
            if self.cmd_options.get("dry", False):
                fname = "Dry {0}".format(step)
            else:
                fname = self.save(step)
                print("hier", fname)
                if fname is None:
                    continue
                if "inode/directory" in props["ftypes"]:
                    dir_times.append((fname, os.stat(fname)))
            fnames.append(fname)
        for dirname, stat in dir_times:
            os.utime(dirname, (stat.st_atime, stat.st_mtime))
        if (not self.cmd_options.get("keep", False) and
                os.path.exists(self.get_tmp(True))):
            shutil.rmtree(self.get_tmp(True))
        return fnames, [self.items[step]["fullname"] for step in orig_steps]

    def get_all_options(self):
        """Show the possible options"""
        all_options = {}
        if not self.finals[0]:
            return all_options
        for plugin in set.union(
                *(self.items[step]["_plugins"] for step in self.finals[0])):
            if plugin not in config.PLUGINS:
                continue
            poptions = config.PLUGINS[plugin]
            if "params" not in poptions:
                continue
            all_options["{forig} => {fdest}".format(
                forig=",".join(poptions["forig"]),
                fdest=",".join(poptions["fdest"]))] = poptions["params"]

        return all_options

    def print_params(self):
        """Show the possible options"""
        outputs = []
        for label, params in self.get_all_options().items():
            outputs.append("{label}\n{params}".format(
                label=label,
                params="\n".join([
                    "  {0:<10s}: {1}".format(param, desc)
                    for param, desc in params.items()])))
        return "\n".join(outputs)

    def menu_params(self, label, params, action=None):
        """Show a menu for the params selection"""

        if "options" not in self.cmd_options:
            self.cmd_options["options"] = []
        options = self.cmd_options["options"]
        if action in options:
            options.remove(action)
        elif action is not None:
            if "=" in action:
                group = action.split("=")[0]
                for option in options:
                    if "=" in option and option.split("=")[0] == group:
                        options.remove(option)
            options.append(action)

        output = "{0}\n".format(label)
        groups = []
        for option, desc, default in params:
            if action is None and default:
                options.append(option)
            if option in options:
                if "=" in option:
                    group = option.split("=")[0]
                    if group in groups:
                        options.remove(option)
                    else:
                        groups.append(group)
            output += "  [{selected}] {option}{desc}\n".format(
                option=option,
                desc="" if desc == "" else ": {0}".format(desc),
                selected="x" if option in options else " ")
        output += "\n"

        os.system("clear")
        sys.stdout.write(output)
        action = six.moves.input("Choose option (done if ready): ")

        return (None if action == "done" else
                self.menu_params(label, params, action))

    def build(self):
        """Find all the paths"""
        if self.dest["ftypes"] is None:
            logger.error("No valid destination")
            return

        self.first_step()

        added = True
        while added:
            added = self.expand_folders()

        added = True
        while added:
            added = self.simple_steps() + self.multi_steps()
        logger.info("\n" + display.get_tree(self))
        logger.debug(tools.Lazy(lambda: "\n" + display.get_tree(self, True)))


def convert_fname(orig, dest, **cmd_options):
    """Convert orig file to new file"""
    tree = Tree(orig, dest, **cmd_options)
    tree.build()
    # logger.debug(tools.Lazy(display.get_items(tree))
    logger.debug(tools.Lazy(lambda: "\n" + display.get_tree(tree, True)))
    logger.info(display.get_tree(tree))
    return tree.save_all()
