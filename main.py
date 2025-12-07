from calendar import c
from typing import List
from crewai.flow.flow import Flow, listen, start, router, and_, or_
from crewai import Agent
from crewai import LLM
from pydantic import BaseModel
from tools import web_search_tool

class BlogPost(BaseModel):
    title: str
    subtitle: str
    sections: List[str]

class Tweet(BaseModel):
    content: str
    hashtags: str

class LinkedInPost(BaseModel):
    hook: str
    content: str
    call_to_acction: str


class ContentPipelineState(BaseModel):
    #inputs
    content_type: str=""
    topic: str=""
    
    #internal
    max_length: int=0
    score: int=0
    research: str=""

    #content
    blog_post: str=""
    tweet: str=""
    linkedin_post: str=""

class ContentPipelineFlow(Flow[ContentPipelineState]):
    @start()
    def init_content_pipeline(self): #validate the state
        if self.state.content_type not in ["tweet", "blog", "linkedin"]:
            raise ValueError("The content type is not valid.")

        if self.state.topic=="":
            raise ValueError("The topic can't be empty.")

        if self.state.content_type == "tweet":
            self.state.max_length = 150
        elif self.state.content_type=="blog":
            self.state.max_length=800
        elif self.state.content_type=="linkedin":
            self.state.max_length=500

    @listen(init_content_pipeline)
    def conduct_research(self):
        researcher = Agent(
            role="Head Researcher",
            backstory="You're like a digital detective who loves digging up fascinating facts and insights. You have a knack for finding the good stuff that others miss.",
            goal=f"Find the most interesting and useful info about {self.state.topic}"
            tools=[web_search_tool]
        )
        self.state.research = researcher.kickoff()

    @router(conduct_research)
    def conduct_research_router(self):
        content_type=self.state.content_type

        if content_type=="blog":
            return "make_blog"
        elif content_type=="tweet":
            return "make_tweet"
        elif content_type=="linkedin":
            return "make_linkedin_post"

    @listen(or_("make_blog", "remake_blog"))
    def handle_make_blog(self):
        """
        if blog post has been made, give the old one to the ai and ask it to improve, else just ask to create a new one.
        """
        print("Making blog...")
        blog_post=self.state.blog_post
        
        llm = LLM(model="openai/gpt-5-mini", response_format=BlogPost) #return type을 강제할 수 있음

        if blog_post=="":
            result = llm.call(f"""
            Make a blog post on the topic {self.state.topic} using the following research:
            
            <research>
            ===============
            {self.state.research}
            ===============
            </research>
            """)
            result.title
        else:
            # improve it


    @listen(or_("make_tweet", "remake_tweet"))
    def handle_make_tweet(self):
        """
        if tweet has been made, give the old one to the ai and ask it to improve, else just ask to create a new one.
        """
        print("Making tweet...")
    
    @listen(or_("make_linkedin_post", "remake_linkedin_post"))
    def handle_make_linkedin_post(self):
        """
        if linkedin post has been made, give the old one to the ai and ask it to improve, else just ask to create a new one.
        """
        print("Making linkedin post...")

    @listen(handle_make_blog)
    def check_seo(self):
        print("Checking Blog SEO...")

    @listen(or_(handle_make_tweet, handle_make_linkedin_post))
    def check_virality(self):
        print("Checking virality...")

    @router(or_(check_seo, check_virality))
    def score_router(self):
        content_type = self.state.content_type
        score = self.state.score

        #if the score is not high enough, remake the post
        if score>=8:
            return "check_passed"
        else:
            if content_type=="blog":
                return "remake_blog"
            elif content_type=="linkedin":
                return "remake_linkedin"
            else:
                return "remake_tweet"

    @listen("check_passed")
    def finalize_content(self):
        print("Finalizing content...")

flow = ContentPipelineFlow()
flow.plot()
# flow.kickoff(inputs={"content_type":"tweet", "topic":"AI and ML"})
