from backend.functions.core.colored_logger import AsyncLogger


def main():
    logger = AsyncLogger()
    logger.b_info("INFO MESSAGE",)
    logger.b_warn("WARN MESSAGE")
    logger.b_err("ERR MESSAGE")
    logger.b_deb("DEBUG MESSAGE")
    logger.b_exc("TRACE MESSAGE")

if __name__ == "__main__":
    main()