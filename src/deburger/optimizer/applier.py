from typing import List, Dict
from dataclasses import dataclass

from deburger.optimizer.fixer import Fix
from deburger.optimizer.validator import FixValidator


@dataclass
class ApplyResult:
    file_path: str
    success: bool
    fixes_applied: int
    error: str = None


class FixApplier:
    def __init__(self, dry_run: bool = False, validate: bool = True):
        self.dry_run = dry_run
        self.validate = validate
        self.validator = FixValidator() if validate else None
        self.applied_count = 0

    def apply_fix(self, fix: Fix) -> ApplyResult:
        # validate fix first
        if self.validate:
            validation = self.validator.validate_fix(fix)
            if not validation["valid"]:
                return ApplyResult(
                    file_path=fix.issue.file_path,
                    success=False,
                    fixes_applied=0,
                    error=f"fix validation failed: {validation['error']}"
                )

        # read current file
        try:
            with open(fix.issue.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return ApplyResult(
                file_path=fix.issue.file_path,
                success=False,
                fixes_applied=0,
                error=f"failed to read file: {e}"
            )

        # replace original code with fixed code
        if fix.original_code not in content:
            return ApplyResult(
                file_path=fix.issue.file_path,
                success=False,
                fixes_applied=0,
                error="original code not found in file (file may have changed)"
            )

        new_content = content.replace(fix.original_code, fix.fixed_code, 1)

        # write back (unless dry run)
        if not self.dry_run:
            # create backup first
            backup_path = self.create_backup(fix.issue.file_path)

            try:
                with open(fix.issue.file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                # validate file after writing
                if self.validate:
                    validation = self.validator.validate_file_after_fix(fix.issue.file_path)
                    if not validation["valid"]:
                        # restore backup
                        if backup_path:
                            with open(backup_path, 'r', encoding='utf-8') as f:
                                original = f.read()
                            with open(fix.issue.file_path, 'w', encoding='utf-8') as f:
                                f.write(original)

                        return ApplyResult(
                            file_path=fix.issue.file_path,
                            success=False,
                            fixes_applied=0,
                            error=f"file validation failed after fix: {validation['error']}"
                        )

            except Exception as e:
                return ApplyResult(
                    file_path=fix.issue.file_path,
                    success=False,
                    fixes_applied=0,
                    error=f"failed to write file: {e}"
                )

        self.applied_count += 1

        return ApplyResult(
            file_path=fix.issue.file_path,
            success=True,
            fixes_applied=1
        )

    async def apply_fixes(self, fixes: List[Fix], auto_only: bool = False) -> Dict:
        # apply multiple fixes in parallel
        import asyncio

        async def apply_one(fix):
            # skip unsafe fixes if auto_only
            if auto_only and not fix.auto_apply_safe:
                return None

            # run in thread pool since file I/O
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.apply_fix, fix)
            return result

        # process all fixes concurrently
        tasks = [apply_one(fix) for fix in fixes]
        all_results = await asyncio.gather(*tasks)

        results = [r for r in all_results if r is not None]
        files_modified = set(r.file_path for r in results if r.success)

        return {
            "total_fixes": len(fixes),
            "applied": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
            "files_modified": len(files_modified),
            "results": results,
            "dry_run": self.dry_run
        }

    def create_backup(self, file_path: str):
        # create backup before applying
        backup_path = f"{file_path}.deburger-backup"
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return backup_path
        except Exception:
            return None
