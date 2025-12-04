from crewai.flow.flow import Flow, listen, start, router, and_, or_
from pydantic import BaseModel

class ContentPipelineState(BaseModel):
    #inputs
    content_type: str=""
    topic: str=""
    
    #internal
    max_length: int=0
    score: int=0

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
        print("Researching...")
        return True

    @router(conduct_research)
    def router(self):
        content_type=self.state.content_type
        if content_type=="blog":
            return "make_blog"
        elif content_type=="tweet":
            return "make_tweet"
        else:
            return "make_linkedin_post"

    @listen("make_blog")
    def handle_make_blog(self):
        print("Making blog...")

    @listen("make_tweet")
    def handle_make_tweet(self):
        print("Making tweet...")
    
    @listen("make_linkedin_post")
    def handle_make_linkedin_post(self):
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
