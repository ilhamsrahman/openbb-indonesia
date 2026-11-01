from openbb_core.provider.abstract.provider import Provider
from .fetchers import IndoEquityHistoricalFetcher

provider = Provider(
    name="indonesia",
    description="Simple Indonesia Data Provider",
    fetcher_dict={"EquityHistorical": IndoEquityHistoricalFetcher},
)