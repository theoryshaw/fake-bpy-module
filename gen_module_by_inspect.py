import os
import sys
import json
import argparse
import inspect
from typing import List, Dict
import importlib


class GenerationConfig:
    output_dir = None


def import_modules(module_name_list: List[str]) -> List:
    imported_modules = []
    for name in module_name_list:
        mod = {}
        mod["module"] = importlib.import_module(name)
        mod["module_name"] = name
        imported_modules.append(mod)
    
    return imported_modules


def analyze_module(module_name: str, module) -> Dict:
    result = {
        "classes": [],
        "functions": [],
        ""
    }

    def analyze_module_internal(module_name: str, module, parent_module_name: str, result: dict):
        this_module_name = "{}.{}".format(parent_module_name, this_module_name)


        members = inspect.getmembers(module)
        for m in members:
            # Sub module.
            if inspect.ismodule(m):
                analyze_module_internal(m[0], m[1], this_module_name, result)

            # Class.
            if inspect.isclass(m):
                if inspect.isbuiltin(m[1]):
                    continue
                if m[1].__module__ != this_module_name:
                    # TODO: this is alias (ex. bpy.types.ANIM_OT_keying_set_export = bl_operators.anim.ANIM_OT_keying_set_export)
                    continue
                result["classes"].append(analyze_class(module_name, c))

            # Function.
            if inspect.isclass(m):
                if m[0].startswith("_"):
                    continue    # Skip private functions.
                if m[1].__module__ != this_module_name:
                    # TODO: this is alias (ex. bpy.types.ANIM_OT_keying_set_export = bl_operators.anim.ANIM_OT_keying_set_export)
                    continue

                result["functions"].append(analyze_function(module_name, f))
    
    analyze_module_internal(module_name, module, module_name, result)

    return result


def analyze(modules: List) -> Dict:
    results = {}
    for m in modules:
        results[m["module_name"]] = analyze_module(m["module_name"], m["module"])

    return results


def write_to_modfile(info: Dict, config: 'GenerationConfig'):
    data = {}

    for module_name, module_info in info.items():
        package_name = module_name
        index = package_name.find(".")
        if index != -1:
            package_name = package_name[:index]

        if package_name not in data.keys():
            data[package_name] = {
                "new": []
            }
        for class_info in module_info["classes"]:
            data[package_name]["new"].append(class_info)
        for function_info in module_info["functions"]:
            data[package_name]["new"].append(function_info)

    os.makedirs(config.output_dir, exist_ok=True)
    for pkg, d in data.items():
        with open("{}/{}.json".format(config.output_dir, pkg), "w") as f:
            json.dump(d, f, indent=4, sort_keys=True, separators=(",", ": "))


def parse_options() -> 'GenerationConfig':
    # Start after "--" option if we run this script from blender binary.
    argv = sys.argv
    try:
        index = argv.index("--") + 1
    except:
        index = len(argv)
    argv = argv[index:]

    usage = """Usage: blender -noaudio --factory-startup --background --python
               {} -- [-o <output_dir>]"""\
        .format(__file__)
    parser = argparse.ArgumentParser(usage)
    parser.add_argument(
        "-o", dest="output_dir", type=str, help="Output directory.", required=True
    )
    args = parser.parse_args(argv)

    config = GenerationConfig()
    config.output_dir = args.output_dir

    return config


def main():
    module_name_list = [
        "bpy",
    ]

    config = parse_options()

    # Import modules.
    imported_modules = import_modules(module_name_list)

    # Analyze modules.
    results = analyze(imported_modules)

    # Write module info to file.
    write_to_modfile(results, config)


if __name__ == "__main__":
    main()
