from crewai.project import CrewBase, agent, task, crew
from crewai import Agent, Task, Crew
from pydantic import BaseModel

class Score(BaseModel):
    score: int
    reason: str

@CrewBase
class ViralityCrew:
    @agent
    def virality_expert(self):
        return Agent(
            role="Social Media Virality Expert",
            goal="Analyze social media content for viral potential and provide a score with actionable feedback",
            backstory="""You are a social media strategist with deep expertise in viral content creation. You've analyzed thousands of  viral posts across Twitter and LinkedIn, understanding the psychology of engagement, shareability, and what makes content spread.
            You know the specific mechanics that drive virality on each platform -- from hook writing to emotional triggers.""",
            verbose=True
        )

        