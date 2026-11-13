from collections import Counter
import pandas as pd
from ...core.contracts import ProcessingResult
from ...services.normalization import normalized, text, email, valid_email, login_problem, ExcelFault, ERRORS

QUALITY_LABELS = {
    "source_rows": "Total source rows",
    "eligible_rows": "Eligible rows",
    "blank_login": "Excluded blank Salesforce Last login",
    "na_login": "Excluded #N/A Salesforce Last login",
    "invalid_login": "Other invalid Salesforce Last login values",
    "missing_email": "Missing email",
    "invalid_email": "Invalid email",
    "blank_market": "Blank market",
    "unapproved_roles": "Unapproved roles",
    "duplicates_removed": "Duplicate occurrences removed",
    "unique_mappings": "Final unique mappings",
    "excluded_rows": "Excluded records before deduplication",
    "unique_accounts": "Unique accounts across all markets",
}
REASONS = {"blank_login": "Blank Salesforce Last login", "na_login": "#N/A Salesforce Last login",
           "invalid_login": "Invalid Salesforce Last login", "unapproved_roles": "Unapproved role",
           "missing_email": "Both email fields missing", "invalid_email": "Invalid account email",
           "blank_market": "Blank or invalid market"}

def process(inputs, config):
    source = inputs["source"]
    approved = {}
    for value in inputs["roles"]["role_code"]:
        key = normalized(value)
        if key and not isinstance(value, ExcelFault) and text(value).upper() not in ERRORS:
            approved.setdefault(key, " ".join(text(value).split()))
    metrics = Counter({key: 0 for key in QUALITY_LABELS})
    metrics["source_rows"] = len(source)
    eligible, excluded, unmatched = [], [], Counter()
    def audit_email(value):
        return text(value) if config.include_full_audit_emails else ("[redacted]" if text(value) else "")
    for reference, row in source.iterrows():
        failure = login_problem(row["login"], config.login_day_first)
        role_key = normalized(row["role"])
        role = approved.get(role_key)
        fds, eip = email(row["fds_email"]), email(row["eip_email"])
        account = fds or eip
        market = " ".join(text(row["market"]).split())
        bad_market = not market or isinstance(row["market"], ExcelFault) or market.upper() in ERRORS
        bad_email = bool(account) and not valid_email(account)
        # Quality flags are independent counts. Exclusion uses the first rule in the pipeline.
        if failure:
            metrics[failure] += 1
        if role is None:
            metrics["unapproved_roles"] += 1
            unmatched[role_key or "(blank)"] += 1
        if not account:
            metrics["missing_email"] += 1
        if bad_email:
            metrics["invalid_email"] += 1
        if bad_market:
            metrics["blank_market"] += 1
        reason = (failure or ("unapproved_roles" if role is None else None)
                  or ("missing_email" if not account else None)
                  or ("invalid_email" if bad_email and config.exclude_invalid_emails else None)
                  or ("blank_market" if bad_market else None))
        if reason:
            all_issues = [k for k, yes in [
                (failure, bool(failure)), ("unapproved_roles", role is None),
                ("missing_email", not account), ("invalid_email", bad_email),
                ("blank_market", bad_market)] if yes]
            excluded.append({"Source Row": int(reference), "Market": market,
                             "FDS JobRole": text(row["role"]),
                             "FDS Email": audit_email(row["fds_email"]),
                             "EIP Email": audit_email(row["eip_email"]),
                             "Salesforce Last login": row["login"],
                             "Exclusion Reason": REASONS[reason],
                             "All Quality Issues": "; ".join(REASONS[k] for k in all_issues)})
        else:
            eligible.append({"Market": market, "Account Role": role, "Account Email": account,
                             "Salesforce Last login": row["login"]})
    mapping_columns = ["Market", "Account Role", "Account Email", "Salesforce Last login"]
    clean = pd.DataFrame(eligible, columns=mapping_columns)
    unique = clean.drop_duplicates(["Market", "Account Role", "Account Email"], keep="first")
    metrics["eligible_rows"] = len(clean)
    metrics["excluded_rows"] = len(excluded)
    metrics["unique_mappings"] = len(unique)
    metrics["duplicates_removed"] = len(clean) - len(unique)
    metrics["unique_accounts"] = int(unique["Account Email"].nunique())
    if len(unique):
        grouped = unique.groupby(["Market", "Account Role"], sort=True)["Account Email"].nunique()
        if config.include_zero_counts:
            # Represented markets = markets with at least one final eligible mapping.
            if unique["Market"].nunique() * len(approved) > 500_000:
                raise ValueError("Zero-count expansion exceeds 500,000 combinations. Disable zero counts.")
            combinations = pd.MultiIndex.from_product(
                [sorted(unique["Market"].unique()), sorted(approved.values())], names=["Market", "Account Role"])
            grouped = grouped.reindex(combinations, fill_value=0)
        counts = grouped.rename("Unique Account Count").reset_index()
        summary = unique.groupby("Market", sort=True).agg(
            **{"Unique Accounts": ("Account Email", "nunique"),
               "Role Assignments": ("Account Email", "size"),
               "Number of Roles": ("Account Role", "nunique")}).reset_index()
        audit = clean.groupby(["Market", "Account Role"], sort=True).agg(
            **{"Original Eligible Rows": ("Account Email", "size"),
               "Unique Accounts": ("Account Email", "nunique")}).reset_index()
        audit["Duplicate Occurrences Removed"] = audit["Original Eligible Rows"] - audit["Unique Accounts"]
    else:
        counts = pd.DataFrame(columns=["Market", "Account Role", "Unique Account Count"])
        summary = pd.DataFrame(columns=["Market", "Unique Accounts", "Role Assignments", "Number of Roles"])
        audit = pd.DataFrame(columns=["Market", "Account Role", "Original Eligible Rows", "Unique Accounts", "Duplicate Occurrences Removed"])
    quality = pd.DataFrame([{"Metric": QUALITY_LABELS[k], "Count": int(v)} for k, v in metrics.items()])
    tables = {
        "Market Summary": summary, "Role Counts": counts,
        "Unique Mapping": unique.sort_values(["Market", "Account Role", "Account Email"]),
        "Duplicate Audit": audit, "Data Quality": quality,
        "Unmatched Roles": pd.DataFrame([{"Unmatched FDS JobRole": role, "Source Row Count": count}
                                        for role, count in sorted(unmatched.items())],
                                       columns=["Unmatched FDS JobRole", "Source Row Count"]),
        "Excluded Records": pd.DataFrame(excluded, columns=["Source Row", "Market", "FDS JobRole", "FDS Email", "EIP Email", "Salesforce Last login", "Exclusion Reason", "All Quality Issues"]),
    }
    return ProcessingResult(tables, dict(metrics), [
        "Role assignments can exceed unique market accounts because one account may have multiple roles.",
        "Quality flags overlap across source rows. Each excluded row has one primary reason and all detected issues.",
        "Eligible rows pass all configured filters, before deduplication. The first source occurrence is retained.",
        "Zero counts cover approved roles in markets with at least one final mapping. Market names are case-sensitive.",
        "Excluded-record emails are " + ("visible by explicit configuration." if config.include_full_audit_emails else "redacted. Unique Mapping contains full account emails."),
    ])
