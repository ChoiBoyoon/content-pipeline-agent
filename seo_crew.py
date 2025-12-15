from crewai.project import CrewBase, agent, task,  crew
from crewai import Agent, Task, Crew

@CrewBase
class SeoCrew:

    @agent
    def seo_expert(self):
        return Agent(
            role = "SEO Specialist",
            goal = "Analyze blog posts for SEO optimization and provide a score with detailed reasoning",
            backstory = """
            You are an experienced SEO specialist with expertise in content optimization.
            You analyze blog posts for keyword usage, meta descriptions, content structure, readability, and search intent alignment to help content rank better in search engines.
            """,
            verbose = True,
        )

    @task
    def seo_audit(self):
        return Task(

        )

    @crew
    def crew(self):
        return Crew(
            agents = self.agents,
            tasks = self.tasks,
            verbose = True
        )