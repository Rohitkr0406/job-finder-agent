import asyncio
from typing import List
from src.models.job import Job
from src.models.resume import ResumeProfile
from src.ai.explainer import explain_job

async def rank_jobs(
    jobs: List[Job],
    resume: ResumeProfile,
    batch_size: int = 3
) -> List[Job]:
    if not jobs:
        return []
        
    sorted_by_py = sorted(jobs, key=lambda j: j.python_score, reverse=True)
    top_40 = sorted_by_py[:40]
    
    top_20 = top_40[:20]
    
    print(f"  [Ranking] Explaining top {len(top_20)} jobs with LLM (from {len(jobs)} candidates) ...")
    
    explained_jobs: List[Job] = []
    total = len(top_20)
    
    for i in range(0, total, batch_size):
        chunk = top_20[i: i + batch_size]
        
        async def explain_staggered(j, delay):
            if delay > 0:
                await asyncio.sleep(delay)
            return await explain_job(j, resume)
            
        tasks = [explain_staggered(j, idx * 0.8) for idx, j in enumerate(chunk)]
        results = await asyncio.gather(*tasks)
        
        for job in results:
            ai_score = job.ai_score if job.ai_score is not None else 0
            job.final_score = 0.7 * job.python_score + 0.3 * ai_score
            explained_jobs.append(job)
            
        done = min(i + batch_size, total)
        print(f"  [Ranking] {done}/{total} explained ...")
        if i + batch_size < total:
            await asyncio.sleep(1.0)
            
    final_ranked = sorted(explained_jobs, key=lambda j: j.final_score, reverse=True)
    return final_ranked
