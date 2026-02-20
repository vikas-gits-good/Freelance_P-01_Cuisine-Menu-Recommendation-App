from Src.Components import ETL_Loader, ETL_Scraper, ETL_Seeder
from Src.Utils import LogException, log_etl

if __name__ == "__main__":
    try:  # this is for local development
        # log_etl.info("Seeder: Preparing seeder")
        # seed = ETL_Seeder()

        # log_etl.info("Seeder: Running seeder")
        # seed.run_seeder()

        # log_etl.info("Seeder: Running upsertion operations")
        # seed.run_upsert()

        # --------------------------------------------------------- #

        log_etl.info("Seeder: Preparing scraper")
        scrp = ETL_Scraper()

        log_etl.info("Seeder: Running scraper")
        scrp.run()

        # --------------------------------------------------------- #

        # log_etl.info("Seeder: Preparing loader")
        # load = ETL_Loader()

        # log_etl.info("Seeder: Running loader")
        # load.run()

    except Exception as e:
        LogException(e, logger=log_etl)
