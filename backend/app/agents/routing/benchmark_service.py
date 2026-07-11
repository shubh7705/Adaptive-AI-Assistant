from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.analytics import ModelBenchmarks
from typing import Dict, List

class BenchmarkService:
    """
    Stage 6: Benchmark Scores
    Fetches benchmark scores from the database.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_benchmarks(self, eligible_ids: List[str] = None) -> Dict[str, ModelBenchmarks]:
        if eligible_ids is not None:
            result = await self.db.execute(select(ModelBenchmarks).where(ModelBenchmarks.model_id.in_(eligible_ids)))
        else:
            result = await self.db.execute(select(ModelBenchmarks))
        benchmarks = result.scalars().all()
        return {b.model_id: b for b in benchmarks}
        
    async def get_benchmark_for_model(self, model_id: str) -> ModelBenchmarks:
        result = await self.db.execute(select(ModelBenchmarks).where(ModelBenchmarks.model_id == model_id))
        return result.scalars().first()
