"""Standard-library verification tests executable without third-party PyPI packages.

Used in restricted environments (e.g. without pip) to verify Python AST syntax,
package layout, Phase 1 modules, and migration presence across apps/api.
"""

from __future__ import annotations

import ast
import pathlib
import unittest

API_ROOT = pathlib.Path(__file__).resolve().parents[1]


class TestApiFoundationSyntaxAndStructure(unittest.TestCase):
    def test_all_python_files_parse_cleanly(self) -> None:
        python_files = (
            list((API_ROOT / "app").rglob("*.py"))
            + list((API_ROOT / "tests").rglob("*.py"))
            + list((API_ROOT / "alembic").rglob("*.py"))
        )
        self.assertGreater(len(python_files), 25)
        for py_file in python_files:
            source = py_file.read_text(encoding="utf-8")
            ast.parse(source, filename=str(py_file))

    def test_phase1_modules_and_migration_exist(self) -> None:
        expected_files = [
            "app/models/enums.py",
            "app/models/user.py",
            "app/models/organization.py",
            "app/models/membership.py",
            "app/models/refresh_session.py",
            "app/models/audit_log.py",
            "app/security/passwords.py",
            "app/security/tokens.py",
            "app/security/rbac.py",
            "app/security/rate_limit.py",
            "app/security/dependencies.py",
            "app/services/audit_service.py",
            "app/services/auth_service.py",
            "app/services/organization_service.py",
            "app/api/v1/endpoints/auth.py",
            "app/api/v1/endpoints/organizations.py",
            "app/api/v1/endpoints/admin.py",
            "alembic/versions/0001_phase1_auth_multitenancy_rls.py",
            "tests/test_auth.py",
            "tests/test_rbac_and_orgs.py",
            "tests/test_tenant_isolation_rls.py",
            "tests/test_security_units.py",
        ]
        for rel in expected_files:
            path = API_ROOT / rel
            self.assertTrue(path.is_file(), f"Missing expected Phase 1 file: {rel}")


if __name__ == "__main__":
    unittest.main()
