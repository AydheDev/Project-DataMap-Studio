import logging

class RedactAccessQuery(logging.Filter):
    """Uvicorn access logs must not record searches containing email addresses."""
    def filter(self, record):
        if isinstance(record.args, tuple) and len(record.args) == 5:
            args = list(record.args)
            args[2] = str(args[2]).split("?", 1)[0]
            record.args = tuple(args)
        return True

def protect_access_logs():
    logger = logging.getLogger("uvicorn.access")
    if not any(isinstance(f, RedactAccessQuery) for f in logger.filters):
        logger.addFilter(RedactAccessQuery())
