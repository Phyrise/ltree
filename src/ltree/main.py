#!/usr/bin/env python3
import os
import sys
import argparse
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from pathlib import Path
import SimpleITK as sitk
import numpy as np
from tqdm import tqdm

MAX_FILES_SHOW = 3
MIN_FOLDERS_TO_COLLAPSE = 4
SUPPORTED_EXTENSIONS = ('.mha', '.nii.gz', '.nii')

def extract_cohort(name):
    match = re.match(r'^([0-9]*[a-zA-Z]+)', name)
    if match:
        prefix = match.group(1)
        return prefix if len(prefix) >= 3 else "Other/Misc"
    return "Other/Misc"

def get_dir_summary(path, show_hidden=False):
    try:
        entries = list(os.scandir(path))
    except PermissionError:
        return 0, 0, []
    
    if not show_hidden:
        entries = [e for e in entries if not e.name.startswith('.')]
        
    dirs = [e for e in entries if e.is_dir()]
    files = sorted([e.name for e in entries if e.is_file()])
    return len(dirs), len(files), files

def get_volume_metadata(filepath):
    try:
        sitk.ProcessObject.SetGlobalDefaultNumberOfThreads(1)
        reader = sitk.ImageFileReader()
        reader.SetFileName(str(filepath))
        reader.ReadImageInformation()
        
        size = reader.GetSize()
        spacing = [round(s, 2) for s in reader.GetSpacing()]
        
        pixel_id = reader.GetPixelID()
        dummy_img = sitk.Image([1] * reader.GetDimension(), pixel_id)
        pixel_id_str = dummy_img.GetPixelIDTypeAsString()
        
        # Clean up and map SimpleITK pixel types to standard types (float32, int64, etc.)
        dtype_map = {
            "32-bit float": "float32",
            "64-bit float": "float64",
            "32-bit signed integer": "int32",
            "64-bit signed integer": "int64",
            "16-bit signed integer": "int16",
            "16-bit unsigned integer": "uint16",
            "8-bit unsigned integer": "uint8",
            "8-bit signed integer": "int8"
        }
        dtype = dtype_map.get(pixel_id_str, pixel_id_str.replace("-bit ", "").replace(" signed ", "").replace(" unsigned ", ""))
        
        return {"shape": size, "spacing": spacing, "dtype": dtype, "error": None}
    except Exception as e:
        return {"error": str(e).replace('\n', ' ')}

def format_file_list(files):
    if not files:
        return ""
    if len(files) <= MAX_FILES_SHOW:
        return f"[{', '.join(files)}]"
    return f"[{files[0]} ... {files[-1]} ({len(files)} files)]"

def scan_entire_dataset(root_path, show_hidden=False):
    all_files = []
    for root, _, files in os.walk(root_path):
        if not show_hidden and any(part.startswith('.') for part in Path(root).parts):
            continue
        for f in files:
            if f.endswith(SUPPORTED_EXTENSIONS):
                all_files.append(Path(root) / f)

    if not all_files:
        print("❌ No matching medical imaging volumes discovered.")
        return

    results = []
    workers = min(8, os.cpu_count() or 4)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(get_volume_metadata, f): f for f in all_files}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="⚡ Scanning volumes", unit="vol", leave=False):
            results.append(fut.result())

    valid_results = [r for r in results if r and r["error"] is None]
    if not valid_results:
        print("❌ Error: Could not retrieve valid metadata from any volumes.")
        return

    shapes = np.array([r["shape"] for r in valid_results])
    spacings = np.array([r["spacing"] for r in valid_results])
    dtypes = Counter([r["dtype"] for r in valid_results])

    min_sh, max_sh = shapes.min(axis=0), shapes.max(axis=0)
    med_sh = np.median(shapes, axis=0).astype(int)
    
    min_sp, max_sp = spacings.min(axis=0), spacings.max(axis=0)
    med_sp = np.median(spacings, axis=0)

    sh_range = f"[{min_sh[0]}-{max_sh[0]}; {min_sh[1]}-{max_sh[1]}; {min_sh[2]}-{max_sh[2]}]"
    sh_med   = f"[{med_sh[0]}, {med_sh[1]}, {med_sh[2]}]"
    
    sp_range = f"[{round(min_sp[0],2)}-{round(max_sp[0],2)}; {round(min_sp[1],2)}-{round(max_sp[1],2)}; {round(min_sp[2],2)}-{round(max_sp[2],2)}]"
    sp_med   = f"[{round(med_sp[0],2)}, {round(med_sp[1],2)}, {round(med_sp[2],2)}]"

    print(f"📊 Dataset Fingerprint ({len(valid_results)} volumes)")
    print(f"  • Types:    {dict(dtypes)}")
    print(f"  • Shapes:   {sh_range} | Median: {sh_med}")
    print(f"  • Spacing:  {sp_range} | Median: {sp_med}")

def print_compressed_tree(root_dir, indent="", show_hidden=False, executor=None, is_last=True):
    root = Path(root_dir)
    try:
        entries = list(os.scandir(root))
    except PermissionError:
        return

    if not show_hidden:
        entries = [e for e in entries if not e.name.startswith('.')]

    entries = sorted(entries, key=lambda e: e.name)
    subdirs = [e for e in entries if e.is_dir()]
    files = [e for e in entries if e.is_file()]

    current_branch = "└── " if is_last else "├── "
    next_indent = indent + ("    " if is_last else "│   ")

    if files:
        med_files = [f.name for f in files if f.name.endswith(SUPPORTED_EXTENSIONS)]
        if med_files:
            meta = get_volume_metadata(root / med_files[0])
            if meta and meta["error"] is None:
                remaining_str = f" (+{len(files) - 1} )" if len(files) > 1 else ""
                meta_str = f" 🔍 {meta['shape']},   spc: {meta['spacing']}, {meta['dtype']}"
                print(f"{indent}{current_branch}📄 {med_files[0]}{remaining_str}{meta_str}")
            elif meta and meta["error"] is not None:
                remaining_str = f" (+{len(files) - 1} )" if len(files) > 1 else ""
                print(f"{indent}{current_branch}📄 {med_files[0]}{remaining_str} 🔍 ⚠️ Error: {meta['error'][:40]}...")
            else:
                print(f"{indent}{current_branch}{format_file_list([f.name for f in files])}")
        else:
            print(f"{indent}{current_branch}{format_file_list([f.name for f in files])}")
        
        if not subdirs:
            return

    if subdirs:
        paths = [d.path for d in subdirs]
        summaries = list(executor.map(lambda p: get_dir_summary(p, show_hidden), paths))
        
        dir_profiles = []
        for d, (d_subdirs, d_files, _) in zip(subdirs, summaries):
            signature = f"dirs:{d_subdirs}_files:{d_files}"
            dir_profiles.append((d, signature))
            
        templated_dirs = {}
        for d, signature in dir_profiles:
            templated_dirs.setdefault(signature, []).append(d)

        items = list(templated_dirs.items())
        for idx, (signature, dir_list) in enumerate(items):
            is_last_group = (idx == len(items) - 1)
            group_branch = "└── " if is_last_group else "├── "
            group_next_indent = indent + ("    " if is_last_group else "│   ")

            if len(dir_list) >= MIN_FOLDERS_TO_COLLAPSE:
                first_dir = dir_list[0]
                last_dir = dir_list[-1]
                cohort_counts = Counter(extract_cohort(d.name) for d in dir_list)
                cohort_str = ", ".join(f"{k}: {v}" for k, v in sorted(cohort_counts.items()))
                
                print(f"{indent}{group_branch}📂 {first_dir.name} ... {last_dir.name} ({len(dir_list)} similar folders | {cohort_str})")
                print_compressed_tree(first_dir.path, group_next_indent, show_hidden, executor, is_last=True)
            else:
                for s_idx, d in enumerate(dir_list):
                    is_last_single = (is_last_group and s_idx == len(dir_list) - 1)
                    single_branch = "└── " if is_last_single else "├── "
                    single_next_indent = indent + ("    " if is_last_single else "│   ")

                    orig_idx = subdirs.index(d)
                    d_subdirs, d_files, _ = summaries[orig_idx]
                    info = f" ({d_subdirs} dirs, {d_files} files)" if d_subdirs or d_files else ""
                    
                    print(f"{indent}{single_branch}📂 {d.name}{info}")
                    print_compressed_tree(d.path, single_next_indent, show_hidden, executor, is_last=is_last_single)

def main():
    parser = argparse.ArgumentParser(description="Concise tree overview and fingerprint tracking for 3D datasets.")
    parser.add_argument("path", nargs="?", default=".", help="Target directory to scan (default: current)")
    parser.add_argument("-a", "--all", action="store_true", help="Show hidden files and folders")
    parser.add_argument("-s", "--scan", action="store_true", help="Scan whole dataset for min/median/max stats across volumes")
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' does not exist.")
        sys.exit(1)

    if args.scan:
        scan_entire_dataset(args.path, show_hidden=args.all)
    else:
        print(f"Summary tree for: {os.path.abspath(args.path)}")
        with ThreadPoolExecutor(max_workers=16) as executor:
            print_compressed_tree(args.path, show_hidden=args.all, executor=executor, is_last=True)

if __name__ == "__main__":
    main()