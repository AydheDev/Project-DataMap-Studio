from .schemas import SOURCE_COLUMNS, ROLE_COLUMNS
from ...services.normalization import normalized, ExcelFault, ERRORS, text

def validate_inputs(inputs, config):
    for key, columns in [("source", SOURCE_COLUMNS), ("roles", ROLE_COLUMNS)]:
        if key not in inputs:
            raise ValueError(f"Missing input: {key}")
        absent = {c["key"] for c in columns} - set(inputs[key].columns)
        if absent:
            raise ValueError(f"Missing required mapped columns in {key}: {', '.join(sorted(absent))}")
    approved = [v for v in inputs["roles"]["role_code"]
                if normalized(v) and not isinstance(v, ExcelFault) and text(v).upper() not in ERRORS]
    if not approved:
        raise ValueError("The approved role list contains no valid role codes.")
