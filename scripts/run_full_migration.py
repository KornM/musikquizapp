#!/usr/bin/env python3
"""
Full Migration Orchestration Script

This script runs all migration steps in the correct order to migrate from
single-tenant to multi-tenant architecture.

Usage:
    python scripts/run_full_migration.py
    python scripts/run_full_migration.py --dry-run
"""

import argparse
import sys
import subprocess


def run_script(script_name, args=None, description=""):
    """
    Run a migration script and check for success.

    Args:
        script_name (str): Name of the script to run
        args (list): Additional arguments to pass to the script
        description (str): Description of what the script does

    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\n{'=' * 70}")
    print(f"Step: {description}")
    print(f"Running: {script_name}")
    print(f"{'=' * 70}\n")

    cmd = ["python", f"scripts/{script_name}"]
    if args:
        cmd.extend(args)

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {description} failed with exit code {e.returncode}")
        return False


def main():
    """Main function to orchestrate the full migration."""
    parser = argparse.ArgumentParser(
        description="Run full migration from single-tenant to multi-tenant"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run all migrations in dry-run mode (no changes made)",
    )
    parser.add_argument(
        "--skip-tenant-setup",
        action="store_true",
        help="Skip default tenant setup (if already exists)",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("MULTI-TENANT MIGRATION")
    print("=" * 70)
    print("\nThis script will migrate your Music Quiz application from")
    print("single-tenant to multi-tenant architecture.")
    print("\nMigration steps:")
    print("  1. Create default tenant")
    print("  2. Migrate admins to default tenant")
    print("  3. Migrate sessions to default tenant")
    print("  4. Migrate participants to global participants")
    print("  5. Migrate answers to include tenant context")

    if args.dry_run:
        print("\n[DRY RUN MODE - No changes will be made]")
    else:
        print("\n⚠️  WARNING: This will modify your database!")
        response = input("\nDo you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Migration cancelled.")
            sys.exit(0)

    # Prepare arguments for child scripts
    script_args = []
    if args.dry_run:
        script_args.append("--dry-run")

    # Step 1: Create default tenant
    if not args.skip_tenant_setup:
        if not run_script(
            "setup_default_tenant.py",
            script_args,
            "Create default tenant for backward compatibility",
        ):
            print("\n✗ Migration failed at step 1")
            sys.exit(1)
    else:
        print("\nSkipping default tenant setup (--skip-tenant-setup)")

    # Step 2: Migrate admins
    if not run_script(
        "migrate_admins.py", script_args, "Migrate admins to multi-tenant model"
    ):
        print("\n✗ Migration failed at step 2")
        sys.exit(1)

    # Step 3: Migrate sessions
    if not run_script(
        "migrate_sessions.py", script_args, "Migrate sessions to multi-tenant model"
    ):
        print("\n✗ Migration failed at step 3")
        sys.exit(1)

    # Step 4: Migrate participants
    if not run_script(
        "migrate_participants.py",
        script_args,
        "Migrate participants to global participant model",
    ):
        print("\n✗ Migration failed at step 4")
        sys.exit(1)

    # Step 5: Migrate answers
    if not run_script(
        "migrate_answers.py", script_args, "Migrate answers to multi-tenant model"
    ):
        print("\n✗ Migration failed at step 5")
        sys.exit(1)

    # Success!
    print("\n" + "=" * 70)
    print("MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 70)

    if args.dry_run:
        print("\nThis was a dry run. Run without --dry-run to apply changes.")
    else:
        print("\nYour Music Quiz application has been successfully migrated")
        print("to multi-tenant architecture.")
        print("\nNext steps:")
        print("  1. Test the application with existing data")
        print("  2. Create additional tenants using the super admin UI")
        print("  3. Create tenant admins for each tenant")
        print("  4. Monitor logs for any issues")

    sys.exit(0)


if __name__ == "__main__":
    main()
