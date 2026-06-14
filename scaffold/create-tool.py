#!/usr/bin/env python3
"""
Scaffold generator CLI for TMHSDigital developer tool repositories.

Thin command-line wrapper over the canonical generation library in
``scaffold/generator.py``. Both this CLI and any second generator delegate to
``generator.generate_repo`` so there is one source of truth for what a
born-green repo looks like (see ``standards/born-green-contract.md``).

Generates a fully standards-compliant repository with all required files,
workflows, manifests, and documentation skeleton, and (by default) registers
it in the meta catalog so a repo cannot be born outside the registry.
"""
import argparse
import sys
from pathlib import Path

# When run as `python scaffold/create-tool.py`, sys.path[0] is the scaffold dir,
# so a plain `import generator` resolves. When imported as part of the package,
# fall back to the qualified path.
try:
    from generator import (
        LICENSE_FILES,
        ScaffoldError,
        generate_repo,
    )
except ImportError:  # pragma: no cover - package-context fallback
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from generator import (  # type: ignore
        LICENSE_FILES,
        ScaffoldError,
        generate_repo,
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scaffold a new TMHSDigital developer tool repository",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create-tool.py --name "Unreal Developer Tools" --description "Cursor plugin for Unreal Engine"
  python create-tool.py --name "AWS MCP Server" --type mcp-server --mcp-server
  python create-tool.py --name "K8s Developer Tools" --mcp-server --skills 5 --rules 3
  python create-tool.py --name "Throwaway" --description test --no-register
        """,
    )
    parser.add_argument("--name", required=True, help="Display name (e.g., 'Unreal Developer Tools')")
    parser.add_argument("--slug", help="Kebab-case identifier (auto-derived from name if omitted)")
    parser.add_argument("--description", required=True, help="One-line description")
    parser.add_argument(
        "--type",
        choices=["cursor-plugin", "mcp-server"],
        default="cursor-plugin",
        help="Repository type (default: cursor-plugin)",
    )
    parser.add_argument("--mcp-server", action="store_true", help="Include MCP server scaffold")
    parser.add_argument("--skills", type=int, default=0, help="Number of placeholder skill directories to create")
    parser.add_argument("--rules", type=int, default=0, help="Number of placeholder rule files to create")
    parser.add_argument(
        "--license",
        choices=list(LICENSE_FILES.keys()),
        default="cc-by-nc-nd-4.0",
        help="License for the generated repo (default: cc-by-nc-nd-4.0)",
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Output directory (default: ./output)",
    )
    parser.add_argument(
        "--author-name",
        default="TMHSDigital",
        help="Author name for plugin.json (default: TMHSDigital)",
    )
    parser.add_argument(
        "--author-email",
        default="contact@users.noreply.github.com",
        help="Author email for plugin.json (default: GitHub no-reply placeholder)",
    )
    parser.add_argument(
        "--no-register",
        action="store_true",
        help=(
            "Do NOT add the repo to registry.json. By default the scaffold "
            "registers every generated repo so none is born outside the catalog. "
            "Use this for throwaway/test generation only."
        ),
    )
    parser.add_argument(
        "--registry-root",
        default=None,
        help=(
            "Override the directory whose registry.json (and derived artifacts) "
            "registration targets. Defaults to the meta-repo root."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        output_dir = generate_repo(
            name=args.name,
            description=args.description,
            slug=args.slug,
            repo_type=args.type,
            mcp_server=args.mcp_server,
            skills=args.skills,
            rules=args.rules,
            license_key=args.license,
            output=args.output,
            author_name=args.author_name,
            author_email=args.author_email,
            register=not args.no_register,
            registry_root=Path(args.registry_root) if args.registry_root else None,
        )
    except ScaffoldError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    slug = output_dir.name
    print(f"\nDone! Repository scaffolded at: {output_dir}")
    print("\nNext steps:")
    print(f"  1. cd {output_dir}")
    print("  2. git init && git add -A && git commit -m 'feat: initial scaffold'")
    print(f"  3. Create GitHub repo: gh repo create TMHSDigital/{slug} --public --source .")
    print("  4. Enable GitHub Pages in Settings > Pages > Source: GitHub Actions")
    if args.no_register:
        print("  5. Register in the catalog: add an entry to registry.json and run sync_from_registry.py")
    else:
        print("  5. Catalog entry added; commit registry.json and the regenerated artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
