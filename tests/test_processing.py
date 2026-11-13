from datetime import datetime
import pytest
import pandas as pd
from app.modules.account_role_mapping.module import AccountRoleMapping
from app.modules.account_role_mapping.schemas import MappingConfig
from app.services.normalization import login_problem, ExcelFault
from app.core.registry import ModuleRegistry

@pytest.mark.parametrize("value,expected", [
    (None, "blank_login"), ("", "blank_login"), ("  ", "blank_login"),
    (float("nan"), "blank_login"), ("#N/A", "na_login"), (" #n/a ", "na_login"),
    (ExcelFault("#N/A"), "na_login"), (ExcelFault("#VALUE!"), "invalid_login"),
    (ExcelFault("#UNCACHED_FORMULA!","=NOW()"), "invalid_login"),
    ("#DIV/0!", "invalid_login"), ("not a date", "invalid_login"), (True, "invalid_login"),
    (0, "invalid_login"), (46000, None), ("2026-10-30", None), ("30/10/2026", None),
    (datetime(2026,10,30), None),
])
def test_login_rules(value, expected):
    assert login_problem(value) == expected

def test_account_mapping_invariants(inputs):
    module = AccountRoleMapping()
    config = MappingConfig()
    module.validate(inputs, config)
    result = module.process(inputs, config)
    assert result.metrics["source_rows"] == 16
    assert result.metrics["eligible_rows"] == 5
    assert result.metrics["unique_mappings"] == 4
    assert result.metrics["duplicates_removed"] == 1
    assert result.metrics["excluded_rows"] == 11
    unique = result.tables["Unique Mapping"]
    assert len(unique[unique["Account Email"] == "alice@example.com"]) == 3
    assert "bob@example.com" in unique["Account Email"].tolist()
    assert unique.iloc[0]["Salesforce Last login"] == datetime(2026,10,30)
    counts = result.tables["Role Counts"]
    assert counts["Unique Account Count"].sum() == len(unique)
    assert len(counts) == 6
    assert (counts[counts["Account Role"] == "Viewer"]["Unique Account Count"] == 0).all()
    summary = result.tables["Market Summary"].set_index("Market")
    assert summary.loc["UK", "Unique Accounts"] == 2
    assert summary.loc["UK", "Role Assignments"] == 3
    assert summary.loc["UK", "Number of Roles"] == 2
    assert result.tables["Duplicate Audit"]["Duplicate Occurrences Removed"].sum() == 1
    assert not result.tables["Excluded Records"].to_string().find("other@example.com") >= 0

def test_options(inputs):
    result = AccountRoleMapping().process(inputs, MappingConfig(
        include_zero_counts=False, include_full_audit_emails=True, exclude_invalid_emails=False))
    assert result.metrics["unique_mappings"] == 5
    assert result.metrics["invalid_email"] == 1
    assert len(result.tables["Role Counts"]) == 3
    assert "other@example.com" in result.tables["Excluded Records"]["FDS Email"].tolist()
    # A populated but invalid FDS address is not replaced by EIP.
    assert "not-an-email" in result.tables["Unique Mapping"]["Account Email"].tolist()

def test_empty_source_and_all_excluded(inputs):
    inputs["source"] = inputs["source"].iloc[:0]
    module = AccountRoleMapping()
    module.validate(inputs, MappingConfig())
    result = module.process(inputs, MappingConfig())
    assert len(result.tables) == 7
    assert all(result.metrics[k] == 0 for k in result.metrics)
    inputs["source"] = pd.DataFrame([["UK", "", "", "", None]],
        columns=["market","role","fds_email","eip_email","login"], index=[2])
    result = module.process(inputs, MappingConfig())
    assert result.metrics["excluded_rows"] == 1
    assert result.metrics["unapproved_roles"] == 1
    assert result.metrics["missing_email"] == 1
    assert result.metrics["blank_login"] == 1

def test_invalid_roles_and_missing_columns(inputs):
    module = AccountRoleMapping()
    inputs["roles"] = pd.DataFrame({"role_code":[None," ",ExcelFault("#N/A")]})
    with pytest.raises(ValueError, match="no valid role"):
        module.validate(inputs, MappingConfig())
    inputs["source"] = inputs["source"].drop(columns=["market"])
    with pytest.raises(ValueError, match="Missing required"):
        module.validate(inputs, MappingConfig())

def test_registry():
    registry = ModuleRegistry()
    registry.register(AccountRoleMapping())
    assert registry.get("account-role-mapping").metadata["version"]
    assert registry.describe()[0]["configuration_schema"]["properties"]["include_zero_counts"]
    with pytest.raises(ValueError):
        registry.register(AccountRoleMapping())
    with pytest.raises(ValueError):
        registry.get("missing")
