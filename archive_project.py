#!/usr/bin/env python3
"""
OmniDesk AI — Project Archiver & Bundler Utility

This script packages the complete OmniDesk AI codebase into:
1. A clean ZIP archive (`omni_desk_ai_archive.zip` / `project_archive.zip`)
   excluding virtual environments, git metadata, caches, and transient database files.
2. A consolidated single-file Markdown archive (`codebase_archive.md`)
   containing directory trees and complete source code for documentation and LLM analysis.
"""

import os
import sys
import zipfile
import datetime
from pathlib import Path

# Base root of the project
ROOT_DIR = Path(__file__).resolve().parent

# Default archive file names
ZIP_NAME = "project_archive.zip"
ALIAS_ZIP_NAME = "omni_desk_ai_archive.zip"
MARKDOWN_BUNDLE_NAME = "codebase_archive.md"

# Directories to exclude from archives
EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    ".pytest_cache",
    "__pycache__",
    ".vscode",
    ".idea",
    "chroma_db",
    "node_modules",
    ".gemini",
}

# Specific files to exclude (e.g. sensitive local secrets or generated archives)
EXCLUDE_FILES = {
    ".env",
    ZIP_NAME,
    ALIAS_ZIP_NAME,
    MARKDOWN_BUNDLE_NAME,
}

# Specific file extensions to exclude from all archives
EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".zip",
    ".tar",
    ".gz",
    ".log",
}

# Binary extensions to exclude specifically from text/markdown bundle
EXCLUDE_TEXT_BUNDLE_EXTENSIONS = {
    ".db",
    ".sqlite",
    ".sqlite3",
    ".bin",
}


def should_include_file(file_path: Path) -> bool:
    """Check if a file should be included in the project archive."""
    rel_path = file_path.relative_to(ROOT_DIR)
    
    # Check if any parent folder is in EXCLUDE_DIRS
    for part in rel_path.parts[:-1]:
        if part in EXCLUDE_DIRS or part.startswith("__pycache__"):
            return False
            
    # Check file name
    if rel_path.name in EXCLUDE_FILES:
        return False
        
    # Check extension
    if file_path.suffix.lower() in EXCLUDE_EXTENSIONS:
        return False
        
    return True


def collect_project_files():
    """Collect all valid project files relative to ROOT_DIR."""
    collected = []
    for root, dirs, files in os.walk(ROOT_DIR):
        # Filter directories in-place to prevent os.walk from descending into them
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith("__pycache__")]
        
        for f in files:
            file_path = Path(root) / f
            if should_include_file(file_path):
                collected.append(file_path)
                
    collected.sort(key=lambda p: str(p.relative_to(ROOT_DIR)).lower())
    return collected


def create_zip_archive(files, zip_path: Path):
    """Create a ZIP archive of the project files."""
    print(f"📦 Creating ZIP archive: {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files:
            rel_path = file_path.relative_to(ROOT_DIR)
            zipf.write(file_path, arcname=str(rel_path).replace("\\", "/"))
    
    size_kb = zip_path.stat().st_size / 1024
    print(f"✅ Created {zip_path.name} ({size_kb:.2f} KB, {len(files)} files)")


def generate_markdown_bundle(files, md_path: Path):
    """Generate a single consolidated Markdown archive file containing directory tree and all code."""
    print(f"📄 Creating single-file Markdown archive: {md_path.name}...")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    text_files = [f for f in files if f.suffix.lower() not in EXCLUDE_TEXT_BUNDLE_EXTENSIONS]
    
    lines = []
    lines.append(f"# OmniDesk AI — Complete Project Codebase Archive")
    lines.append(f"> Generated on: `{timestamp}` | Total Files: `{len(text_files)}` (Binary files excluded from text dump)\n")
    lines.append("## Table of Contents")
    for file_path in text_files:
        rel_str = str(file_path.relative_to(ROOT_DIR)).replace("\\", "/")
        anchor = rel_str.lower().replace("/", "").replace(".", "").replace("-", "").replace("_", "")
        lines.append(f"- [{rel_str}](#{anchor})")
    
    lines.append("\n---\n")
    
    for file_path in text_files:
        rel_str = str(file_path.relative_to(ROOT_DIR)).replace("\\", "/")
        anchor = rel_str.lower().replace("/", "").replace(".", "").replace("-", "").replace("_", "")
        suffix = file_path.suffix.lower()
        
        # Determine language for markdown block
        lang_map = {
            ".py": "python",
            ".html": "html",
            ".css": "css",
            ".js": "javascript",
            ".json": "json",
            ".md": "markdown",
            ".toml": "toml",
            ".txt": "text",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".dockerignore": "dockerignore",
            ".gitignore": "gitignore",
        }
        lang = lang_map.get(suffix, "")
        
        lines.append(f"### <a id=\"{anchor}\"></a> `{rel_str}`")
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            lines.append(f"```{lang}")
            lines.append(content)
            lines.append("```\n")
        except Exception as e:
            lines.append(f"*(Binary or unreadable file: {e})*\n")
            
    md_path.write_text("\n".join(lines), encoding="utf-8")
    size_kb = md_path.stat().st_size / 1024
    print(f"✅ Created {md_path.name} ({size_kb:.2f} KB)")


def main():
    print("🚀 OmniDesk AI Archiver Initializing...")
    files = collect_project_files()
    print(f"Found {len(files)} project files to archive.")
    
    # 1. Create primary zip
    zip_dest = ROOT_DIR / ZIP_NAME
    create_zip_archive(files, zip_dest)
    
    # 2. Create alias named zip for convenience
    alias_dest = ROOT_DIR / ALIAS_ZIP_NAME
    create_zip_archive(files, alias_dest)
    
    # 3. Create consolidated markdown codebase archive
    md_dest = ROOT_DIR / MARKDOWN_BUNDLE_NAME
    generate_markdown_bundle(files, md_dest)
    
    print("\n🎉 All archive files created successfully!")


if __name__ == "__main__":
    main()
